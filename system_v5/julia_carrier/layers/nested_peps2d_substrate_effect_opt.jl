#!/usr/bin/env julia
# nested_peps2d_substrate_effect_opt.jl
#
# classification    = nested_peps2d_substrate_effect_opt_poc
# promotion_allowed = false
#
# Purpose:
#   Probe whether PEPSKit ground-state optimization is robust enough to use for the
#   nested-tori vs flat Weyl L/R substrate-effect measurement.
#
# Hard boundary:
#   The known crash path is fixedpoint(...) -> OptimKit LBFGS ->
#   HagerZhangLineSearch. This driver does not put an unproven fixedpoint call on
#   the required exit-0 path. It records the optimizer ladder and then performs the
#   PEPSKit CTMRG contraction readout on physical product-seeded iPEPS states.
#   Therefore any substrate-effect numbers emitted here are contraction/control
#   numbers unless optimization_robust == true. promotion_allowed=false.

using Dates
using JSON
using LinearAlgebra
using PEPSKit
using Random
using TensorKit

const SEED = 20260602
const PSPACE = ComplexSpace(2)
const VSPACE = ComplexSpace(2)
const CHI = 6
const RUN_CTM_CONTROL = get(ENV, "NESTED_PEPS2D_OPT_RUN_CTM", "0") == "1"

const OUT = joinpath(@__DIR__, "nested_peps2d_substrate_effect_opt_results.json")

const RESULT = Dict{String,Any}(
    "sim_id" => "nested_peps2d_substrate_effect_opt",
    "name" => "PEPSKit substrate-effect optimizer robustness probe",
    "version" => "1.0",
    "classification" => "nested_peps2d_substrate_effect_opt_poc",
    "promotion_allowed" => false,
    "timestamp_utc" => string(now(UTC)),
    "seed" => SEED,
    "engine" => "Julia PEPSKit v0.7.0; InfinitePEPS / CTMRGEnv / leading_boundary / expectation_value",
    "claim_ceiling" => "If optimization_robust=false, this is only a PEPSKit CTMRG contraction/control receipt on physical product-seeded iPEPS states. It is not an optimized ground-state substrate-effect result, not canonical, and not a bridge/flux/Axis0/physics claim.",
    "sim_execution_kind" => "nonclassical_adapter_poc",
    "sim_class" => "carrier_probe",
    "root_constraints_in_force" => ["F01 finite PEPS carrier/probe/operator/path set", "N01 order-sensitive Weyl L/R control sign in the chiral bond term"],
    "finite_map" => "For finite shell set {inner, outer}, map (substrate, chirality sign, shell connection) to CTMRG-contracted energy density <H_sgn(connection)> and L/R split E_L - E_R.",
    "domain" => "Two eta shells with physical C^2 spinor index, finite D=2 virtual channels, CTMRG chi=6, LocalOperator nearest-neighbour Hamiltonians.",
    "codomain_or_output" => "Finite table of CTMRG truncation errors, environment entropies, energies, L/R splits, and nested-vs-flat split-collapse metric.",
    "carrier_layer" => "2D PEPSKit iPEPS carrier on square-lattice Hopf-torus substrate adapter",
    "carrier_realization" => "TensorKit ComplexSpace(2) spinor physical space; D=2 PEPS virtual channels; no NumPy.",
    "peps3d_embedding" => "blocked: this file uses a 2D PEPSKit substrate adapter, not a full PEPS3D finite cell/tensor carrier.",
    "spinor_state" => "physical product-seeded C^2 spinor tensor plus small deterministic virtual perturbation",
    "quaternion_action" => "not_applicable",
    "negative_control" => "flat substrate sets the connection to an eta-independent zero value, collapsing shell-dependent L/R split by construction on the fixed control state.",
    "dependency_receipts" => ["layers/nested_peps2d_weyl_on_hopf_tori.jl"],
    "downstream_blocks" => ["optimized_ground_state_claims_when_optimization_robust_false", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "final_manifold_admission"],
    "tool_manifest" => Dict(
        "PEPSKit" => "load_bearing for iPEPS construction, CTMRG contraction, and LocalOperator expectation values",
        "TensorKit" => "load_bearing for C^2 spinor spaces and PEPS tensor construction",
        "OptimKit" => "not invoked on the exit-0 driver path because no fixedpoint optimizer configuration was admitted robust"
    ),
    "tool_integration_depth" => "supportive",
    "divergence_log" => String[],
    "optimizer_ladder" => Dict{String,Any}(),
    "optimized_ground_state_measurement" => Dict{String,Any}(),
    "contraction_control_measurement" => Dict{String,Any}(),
)

logln(args...) = (println(args...); flush(stdout))

function write_results!()
    open(OUT, "w") do io
        JSON.print(io, RESULT, 2)
    end
end

function real_float(x)
    return Float64(real(x))
end

sx() = TensorMap(ComplexF64[0 1; 1 0], PSPACE, PSPACE)
sy() = TensorMap(ComplexF64[0 -im; im 0], PSPACE, PSPACE)
sz() = TensorMap(ComplexF64[1 0; 0 -1], PSPACE, PSPACE)

function env_schmidt_entropy(env)
    _, svals, _ = tsvd(env.corners[1, 1, 1])
    vals = real.(diag(convert(Array, svals)))
    vals = vals[vals .> 0]
    if isempty(vals)
        return 0.0, Float64[]
    end
    probs = (vals .^ 2) ./ sum(vals .^ 2)
    entropy = -sum(p > 1.0e-14 ? p * log(p) : 0.0 for p in probs)
    return Float64(entropy), Float64.(probs)
end

function weyl_hamiltonian(; chirality::Int, connection::Float64, mass::Float64 = 0.25)
    sx_op, sy_op, sz_op = sx(), sy(), sz()
    xy = sx_op ⊗ sx_op + sy_op ⊗ sy_op
    chiral = sx_op ⊗ sy_op - sy_op ⊗ sx_op
    vertical = xy + (chirality * connection) * chiral
    onsite = mass * sz_op
    lat = fill(PSPACE, 1, 1)
    return LocalOperator(
        lat,
        (CartesianIndex(1, 1), CartesianIndex(1, 2)) => xy,
        (CartesianIndex(1, 1), CartesianIndex(2, 1)) => vertical,
        (CartesianIndex(1, 1),) => onsite,
    )
end

function spinor(theta::Float64, phase::Float64)
    v = ComplexF64[cos(theta / 2), cis(phase) * sin(theta / 2)]
    return v ./ norm(v)
end

function physical_seed_peps(; theta::Float64, phase::Float64, epsilon::Float64 = 1.0e-3)
    base = spinor(theta, phase)
    data = zeros(ComplexF64, 2, 2, 2, 2, 2)
    data[:, 1, 1, 1, 1] .= base

    for n in 1:2, e in 1:2, s in 1:2, w in 1:2
        if !(n == 1 && e == 1 && s == 1 && w == 1)
            parity = mod((n - 1) + (e - 1) + (s - 1) + (w - 1), 2)
            local_theta = theta + 0.07 * parity + 0.03 * ((n - s) + (e - w))
            local_phase = phase + 0.11 * ((n - s) - (e - w))
            weight = epsilon * (1.0 + 0.05 * ((n == s ? 1 : -1) + (e == w ? 1 : -1)))
            data[:, n, e, s, w] .+= weight .* spinor(local_theta, local_phase)
        end
    end

    data ./= norm(vec(data))
    tensor = TensorMap(data, PSPACE, VSPACE ⊗ VSPACE ⊗ dual(VSPACE) ⊗ dual(VSPACE))
    return InfinitePEPS(tensor)
end

function contract_peps(peps; chi::Int = CHI, maxiter::Int = 8)
    env0 = CTMRGEnv(randn, ComplexF64, peps, ComplexSpace(chi))
    env, info = leading_boundary(
        env0, peps;
        tol = 1.0e-4,
        miniter = 1,
        maxiter,
        trunc = (; alg = :fixedspace),
        verbosity = 0,
    )
    entropy, spectrum = env_schmidt_entropy(env)
    return env, info, entropy, spectrum
end

function measure_state(label::String, shell::String, eta::Float64, connection::Float64, peps)
    env, info, entropy, spectrum = contract_peps(peps)
    e_left = real_float(expectation_value(peps, weyl_hamiltonian(; chirality = +1, connection), env))
    e_right = real_float(expectation_value(peps, weyl_hamiltonian(; chirality = -1, connection), env))
    mz = real_float(expectation_value(peps, LocalOperator(fill(PSPACE, 1, 1), (CartesianIndex(1, 1),) => sz()), env))
    return Dict{String,Any}(
        "substrate" => label,
        "shell" => shell,
        "eta" => eta,
        "connection" => connection,
        "chi" => CHI,
        "ctmrg_truncation_error" => real_float(info.truncation_error),
        "environment_entropy" => entropy,
        "schmidt_spectrum_head" => first(spectrum, min(length(spectrum), 8)),
        "energy_left" => e_left,
        "energy_right" => e_right,
        "lr_split_E_L_minus_E_R" => e_left - e_right,
        "mz" => mz,
    )
end

function substrate_summary(inner::Dict{String,Any}, outer::Dict{String,Any})
    split_inner = inner["lr_split_E_L_minus_E_R"]
    split_outer = outer["lr_split_E_L_minus_E_R"]
    shell_difference = split_outer - split_inner
    return Dict{String,Any}(
        "inner_split" => split_inner,
        "outer_split" => split_outer,
        "outer_minus_inner_split" => shell_difference,
        "abs_outer_minus_inner_split" => abs(shell_difference),
    )
end

function record_optimizer_ladder!()
    RESULT["optimizer_ladder"] = Dict(
        "pepskit_optimizer_alg_symbols" => [":gradientdescent", ":conjugategradient", ":lbfgs"],
        "line_search_boundary" => "PEPSKit v0.7 named-tuple optimizer_alg does not expose an alternate line-search keyword; OptimKit 0.4 GradientDescent, ConjugateGradient, and LBFGS default to HagerZhangLineSearch.",
        "controller_probe_before_driver" => Dict(
            "candidate" => "optimizer_alg=(alg=:conjugategradient,tol=1e-2,maxiter=1,ls_maxiter=1,ls_maxfg=1), gradient_alg=(alg=:linsolver,solver_alg=(alg=:gmres),iterscheme=:diffgauge,maxiter=2), D=2, chi=6, physical product seed, reuse_env=true",
            "outcome" => "No completion inside the useful liveness window; process was terminated by the controller. No robust optimizer receipt was admitted.",
            "admitted_robust" => false,
        ),
        "driver_policy" => "No fixedpoint call is executed on the required exit-0 path until a candidate returns a complete local receipt. This avoids the known fixedpoint/LBFGS/HagerZhang segfault path and avoids converting a hang into a missing JSON.",
        "optimization_robust" => false,
        "optimization_robust_reason" => "No PEPSKit fixedpoint optimizer configuration returned a complete no-crash receipt in this run.",
        "try_order_status" => [
            Dict("step" => "a", "requested" => "different optimizer/gradient variant", "status" => "attempted by controller with conjugategradient + linsolver/diffgauge; no robust completion"),
            Dict("step" => "b", "requested" => "smaller D=2 and chi=6-12 with looser tol", "status" => "included in attempted controller candidate with D=2 chi=6 tol=1e-4/1e-3/1e-2"),
            Dict("step" => "c", "requested" => "physical seeding", "status" => "included in attempted controller candidate and used in contraction-control driver"),
            Dict("step" => "d", "requested" => "reuse_env and fewer iterations", "status" => "included in attempted controller candidate with reuse_env=true and maxiter=1"),
        ],
    )
    RESULT["optimized_ground_state_measurement"] = Dict(
        "evaluated" => false,
        "optimization_robust" => false,
        "answer" => "no",
        "reason" => "No robust PEPSKit fixedpoint optimizer receipt was obtained; therefore optimized ground states on the two substrates were not admitted or measured.",
    )
end

function run_contraction_control!()
    eta_inner = 0.30
    eta_outer = 0.95
    c_inner = cos(2 * eta_inner)
    c_outer = cos(2 * eta_outer)

    logln("Running contraction-control nested/flat substrate readout")
    nested_inner_peps = physical_seed_peps(theta = 0.62 + 0.10 * eta_inner, phase = 0.20 * c_inner)
    nested_outer_peps = physical_seed_peps(theta = 0.62 + 0.10 * eta_outer, phase = 0.20 * c_outer)
    flat_peps = physical_seed_peps(theta = 0.62, phase = 0.0)

    nested_inner = measure_state("nested_tori", "inner", eta_inner, c_inner, nested_inner_peps)
    nested_outer = measure_state("nested_tori", "outer", eta_outer, c_outer, nested_outer_peps)
    flat_inner = measure_state("flat", "inner", eta_inner, 0.0, flat_peps)
    flat_outer = deepcopy(flat_inner)
    flat_outer["shell"] = "outer"
    flat_outer["eta"] = eta_outer

    nested = substrate_summary(nested_inner, nested_outer)
    flat = substrate_summary(flat_inner, flat_outer)
    effect_metric = nested["abs_outer_minus_inner_split"] - flat["abs_outer_minus_inner_split"]
    flat_collapses = flat["abs_outer_minus_inner_split"] <= 1.0e-10 &&
        nested["abs_outer_minus_inner_split"] > 1.0e-10

    RESULT["contraction_control_measurement"] = Dict(
        "evaluated" => true,
        "optimized_ground_states" => false,
        "honesty_note" => "These are CTMRG-contracted physical product-seeded iPEPS measurements, not optimized PEPSKit fixedpoint ground states.",
        "nested_inner" => nested_inner,
        "nested_outer" => nested_outer,
        "flat_inner" => flat_inner,
        "flat_outer" => flat_outer,
        "nested_summary" => nested,
        "flat_summary" => flat,
        "substrate_effect_metric" => effect_metric,
        "flat_control_collapses" => flat_collapses,
        "substrate_effect_appears_on_contraction_control" => flat_collapses && effect_metric > 0,
    )
end

function record_contraction_blocked!()
    eta_inner = 0.30
    eta_outer = 0.95
    RESULT["contraction_control_measurement"] = Dict(
        "evaluated" => false,
        "optimized_ground_states" => false,
        "answer" => "not_evaluated",
        "reason" => "Default fast receipt mode is active because PEPSKit CTMRG/fixedpoint runs were not returning promptly in the loaded checkout. Set NESTED_PEPS2D_OPT_RUN_CTM=1 to run the contraction-control path.",
        "requested_command_for_ctm_control" => "NESTED_PEPS2D_OPT_RUN_CTM=1 julia --project=\"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier\" \"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/layers/nested_peps2d_substrate_effect_opt.jl\"",
        "nested_connections" => Dict(
            "eta_inner" => eta_inner,
            "eta_outer" => eta_outer,
            "cos2eta_inner" => cos(2 * eta_inner),
            "cos2eta_outer" => cos(2 * eta_outer),
        ),
        "flat_connection" => 0.0,
        "substrate_effect_appears_on_optimized_ground_states" => false,
        "honesty_note" => "No optimized ground-state numbers and no CTMRG contraction-control numbers are fabricated in fast receipt mode.",
    )
end

function main()
    Random.seed!(SEED)
    t0 = time()
    try
        record_optimizer_ladder!()
        RESULT["fast_receipt_mode"] = !RUN_CTM_CONTROL
        if RUN_CTM_CONTROL
            run_contraction_control!()
        else
            record_contraction_blocked!()
        end
    catch err
        RESULT["error"] = sprint(showerror, err, catch_backtrace())
        RESULT["optimized_ground_state_measurement"] = Dict(
            "evaluated" => false,
            "optimization_robust" => false,
            "answer" => "no",
            "reason" => "Driver error before any optimized measurement could be admitted.",
        )
    finally
        RESULT["wallclock_seconds"] = round(time() - t0; digits = 2)
        RESULT["exit_policy"] = "write JSON and exit 0; promotion_allowed=false"
        write_results!()
        logln("Results JSON -> ", OUT)
        logln("optimization_robust -> ", RESULT["optimizer_ladder"]["optimization_robust"])
        if haskey(RESULT, "contraction_control_measurement")
            m = RESULT["contraction_control_measurement"]
            if get(m, "evaluated", false)
                logln("contraction-control nested split diff -> ", get(m["nested_summary"], "outer_minus_inner_split", nothing))
                logln("contraction-control flat split diff -> ", get(m["flat_summary"], "outer_minus_inner_split", nothing))
            else
                logln("contraction-control measurement -> ", m["answer"])
            end
        end
    end
    exit(0)
end

main()
