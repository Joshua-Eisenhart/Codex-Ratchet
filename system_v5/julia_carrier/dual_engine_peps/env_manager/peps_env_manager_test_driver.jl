using Dates
using JSON
using LinearAlgebra
using PEPSKit
using Random
using TensorKit

include("peps_env_manager.jl")
using .PEPSEnvManagerInfra

const HERE = @__DIR__
const RESULT = joinpath(HERE, "peps_env_manager_results.json")
const RUN_SELF_KILL_SECONDS = 210.0
const TEST_CHI = 2
const TEST_CTM_MAXITER = 4
const TEST_CTM_MINITER = 1
const TEST_CTM_TOL = 1.0e-5

function arm_run_watchdog!()
    armed = Ref(true)
    timer = Timer(RUN_SELF_KILL_SECONDS) do _t
        if armed[]
            partial = Dict{String,Any}(
                "object_id" => "peps_env_manager",
                "classification" => "env_manager_infra",
                "promotion_allowed" => false,
                "exit_status" => "timeout_self_kill",
                "self_kill_seconds" => RUN_SELF_KILL_SECONDS,
                "claim_ceiling" => "environment-manager infrastructure only; no physics, layer, bridge, flux, Axis0, or manifold admission claim",
            )
            open(RESULT, "w") do io
                JSON.print(io, partial, 2)
            end
            flush(stdout)
            flush(stderr)
            ccall(:exit, Cvoid, (Cint,), 124)
        end
    end
    return armed, timer
end

function random_tensor(seed::Int)
    rng = MersenneTwister(seed)
    A = randn(rng, ComplexF64, 2, 2, 2, 2, 2)
    return A ./ norm(vec(A))
end

function mutate_tensor(A)
    B = copy(A)
    B[1, 1, 1, 1, 1] += 0.173 + 0.029im
    return B ./ norm(vec(B))
end

function cache_event(label::String, mgr::PEPSEnvManager)
    return Dict{String,Any}(
        "label" => label,
        "status" => string(mgr.last_status),
        "miss_reason" => mgr.last_miss_reason,
        "recompute_count" => mgr.recompute_count,
        "state_hash" => mgr.state_hash,
        "hash_seconds" => round(mgr.last_hash_seconds, digits = 6),
        "recompute_seconds" => round(mgr.last_recompute_seconds, digits = 6),
        "cached_chi" => mgr.cached_chi,
    )
end

function test_kwargs()
    return (;
        chi = TEST_CHI,
        tol = TEST_CTM_TOL,
        miniter = TEST_CTM_MINITER,
        maxiter = TEST_CTM_MAXITER,
        verbosity = 0,
    )
end

function run_driver()
    started_wall = time()
    started_at = now()
    watchdog_armed, watchdog_timer = arm_run_watchdog!()

    result = Dict{String,Any}(
        "object_id" => "peps_env_manager",
        "classification" => "env_manager_infra",
        "promotion_allowed" => false,
        "claim_ceiling" => "environment-manager infrastructure only; no physics, layer, bridge, flux, Axis0, or manifold admission claim",
        "created_at" => string(started_at),
        "ctmrg_settings" => Dict(
            "chi" => TEST_CHI,
            "tol" => TEST_CTM_TOL,
            "miniter" => TEST_CTM_MINITER,
            "maxiter" => TEST_CTM_MAXITER,
            "trunc" => "fixedspace",
            "solver_path" => "CTMRGEnv(peps, ComplexSpace(chi)) -> leading_boundary(...); no fixedpoint, no PEPSOptimize, no LBFGS",
        ),
        "state_cache_design" => Dict(
            "manager_fields" => ["peps_ref", "cached_env", "state_hash", "recompute_count"],
            "extra_guard_fields" => ["cached_chi", "last_status", "last_hash_seconds", "last_recompute_seconds", "last_miss_reason"],
            "cache_key" => "SHA-256 over dense TensorMap payload bytes plus chi",
            "pointer_tradeoff" => "peps_ref is retained for diagnostics only; cache admission does not depend on pointer identity",
            "ad_boundary" => "get_env mutates the manager by owner API design; get_env_cow returns a copied manager for copy-on-write AD-style use",
        ),
        "tool_manifest" => Dict(
            "PEPSKit" => "load_bearing: CTMRGEnv, leading_boundary, expectation_value, InfinitePEPS",
            "TensorKit" => "load_bearing: ComplexSpace and TensorMap carrier with P<-N,E,S,W convention",
            "SHA" => "load_bearing: robust full tensor-data checksum",
            "JSON" => "load_bearing: result receipt",
            "LinearAlgebra" => "supportive: tensor normalization",
            "Random" => "supportive: deterministic fixtures",
        ),
        "tool_integration_depth" => Dict(
            "PEPSKit" => "load_bearing",
            "TensorKit" => "load_bearing",
            "SHA" => "load_bearing",
            "JSON" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "Random" => "supportive",
        ),
        "tests" => Dict{String,Any}(),
        "cache_events" => Any[],
        "checksum_cost" => Dict{String,Any}(),
        "pepskit_env_api" => Dict{String,Any}(),
        "couple_layers_stub" => Dict{String,Any}(),
        "exit_status" => "running",
    )

    try
        println("[warmup] PEPSKit CTMRG low-chi compile/contraction warmup")
        warm_mgr = PEPSEnvManager()
        warm_peps = build_single_site_peps(random_tensor(1001))
        warm_t0 = time()
        get_env(warm_mgr, warm_peps; test_kwargs()...)
        result["warmup"] = Dict(
            "status" => string(warm_mgr.last_status),
            "seconds" => round(time() - warm_t0, digits = 6),
            "recompute_count" => warm_mgr.recompute_count,
        )

        A0 = random_tensor(2002)
        A1 = mutate_tensor(A0)
        peps = build_single_site_peps(A0)
        mgr = PEPSEnvManager()

        println("[test 1] first get_env miss, second get_env hit on same state")
        get_env(mgr, peps; test_kwargs()...)
        first = cache_event("same_state_first_get", mgr)
        push!(result["cache_events"], first)
        count_after_first = mgr.recompute_count

        get_env(mgr, peps; test_kwargs()...)
        second = cache_event("same_state_second_get", mgr)
        push!(result["cache_events"], second)
        test_same_hit = (first["status"] == "miss" &&
            second["status"] == "hit" &&
            count_after_first == 1 &&
            mgr.recompute_count == 1)
        result["tests"]["same_state_second_hit"] = Dict(
            "pass" => test_same_hit,
            "first_status" => first["status"],
            "second_status" => second["status"],
            "recompute_count_after_first" => count_after_first,
            "recompute_count_after_second" => mgr.recompute_count,
        )

        println("[test 2] mutate same PEPS object's site tensor, then require miss")
        peps.A[1, 1] = build_site_tensor(A1)
        get_env(mgr, peps; test_kwargs()...)
        mutation = cache_event("same_object_after_tensor_mutation", mgr)
        push!(result["cache_events"], mutation)
        test_mutation_miss = (mutation["status"] == "miss" &&
            mutation["miss_reason"] == "state_hash_changed" &&
            mgr.recompute_count == 2)
        result["tests"]["mutation_triggers_miss"] = Dict(
            "pass" => test_mutation_miss,
            "status" => mutation["status"],
            "miss_reason" => mutation["miss_reason"],
            "recompute_count_after_mutation" => mgr.recompute_count,
        )

        println("[test 3] hash distinguishes different states and matches identical states")
        h0, h0_seconds = peps_state_hash_timed(build_single_site_peps(A0))
        h0_copy, h0_copy_seconds = peps_state_hash_timed(build_single_site_peps(copy(A0)))
        h1, h1_seconds = peps_state_hash_timed(build_single_site_peps(A1))
        hash_pass = (h0 == h0_copy) && (h0 != h1)
        result["tests"]["hash_distinguishes_states"] = Dict(
            "pass" => hash_pass,
            "same_tensor_hash_equal" => h0 == h0_copy,
            "different_tensor_hash_different" => h0 != h1,
            "hash_A0" => h0,
            "hash_A0_copy" => h0_copy,
            "hash_A1" => h1,
        )

        recompute_times = [ev["recompute_seconds"] for ev in result["cache_events"] if ev["status"] == "miss"]
        hash_times = [first["hash_seconds"], second["hash_seconds"], mutation["hash_seconds"],
            round(h0_seconds, digits = 6), round(h0_copy_seconds, digits = 6), round(h1_seconds, digits = 6)]
        avg_hash = isempty(hash_times) ? 0.0 : sum(hash_times) / length(hash_times)
        avg_recompute = isempty(recompute_times) ? 0.0 : sum(recompute_times) / length(recompute_times)
        result["checksum_cost"] = Dict(
            "hash_seconds_samples" => hash_times,
            "recompute_seconds_samples" => recompute_times,
            "avg_hash_seconds" => round(avg_hash, digits = 6),
            "avg_recompute_seconds" => round(avg_recompute, digits = 6),
            "hash_to_recompute_ratio" => avg_recompute == 0.0 ? nothing : round(avg_hash / avg_recompute, digits = 8),
            "note" => "Full-state SHA-256 is robust against in-place tensor replacement but scales with tensor payload size; pointer tracking would be cheaper but missed by same-object mutation.",
        )

        println("[stub] pseudo-3D two-layer coupling hook uses both layer env managers")
        layer_b = build_single_site_peps(random_tensor(3003))
        mgr_b = PEPSEnvManager()
        coupling = couple_layers(mgr, peps, mgr_b, layer_b;
            chi = TEST_CHI,
            tol = TEST_CTM_TOL,
            miniter = TEST_CTM_MINITER,
            maxiter = TEST_CTM_MAXITER,
            verbosity = 0,
            coupling_strength = 0.25)
        result["couple_layers_stub"] = coupling

        result["pepskit_env_api"] = Dict(
            "exposes_needed_for_per_layer_cache" => true,
            "needed_api_observed" => [
                "InfinitePEPS stores site tensors in field :A",
                "CTMRGEnv(peps, ComplexSpace(chi)) initializes a per-layer environment",
                "leading_boundary(env0, peps; kwargs...) returns a cacheable environment",
                "expectation_value(peps, LocalOperator, env) consumes the returned environment",
            ],
            "gaps_or_cautions" => [
                "No state dirty flag or checksum API was observed; the manager must hash TensorMap payload bytes.",
                "No native pseudo-3D stacked-layer environment object was observed; cross-layer NiTe/SeTi remains a stub/mean-field placement here.",
                "The mutable manager API is convenient but not AD-pure; use get_env_cow for copy-on-write manager replacement in differentiable lanes.",
                "PEPSKit CTMRG info is cached as returned, but this driver does not promote convergence or physics claims.",
            ],
        )

        all_pass = all(v -> v isa Dict && get(v, "pass", false), values(result["tests"]))
        result["all_tests_pass"] = all_pass
        result["exit_status"] = all_pass ? "ok" : "failed_tests"
    catch e
        result["exit_status"] = "error"
        result["error"] = sprint(showerror, e, catch_backtrace())
    finally
        result["wall_seconds"] = round(time() - started_wall, digits = 6)
        result["completed_at"] = string(now())
        open(RESULT, "w") do io
            JSON.print(io, result, 2)
        end
        watchdog_armed[] = false
        close(watchdog_timer)
    end

    println("Wrote $(RESULT)")
    println("exit_status=$(result["exit_status"]) wall_seconds=$(result["wall_seconds"])")
    println("tests=$(JSON.json(result["tests"]))")
    return result
end

run_driver()
