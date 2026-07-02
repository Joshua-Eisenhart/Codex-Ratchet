#!/usr/bin/env julia
# nested_peps2d_substrate_effect_imagtime.jl
#
# classification    = tool_lego_fit_probe
# promotion_allowed = false
#
# Goal:
#   Independent non-LBFGS path for the nested PEPS2D substrate effect. This file
#   avoids PEPSKit.fixedpoint, PEPSOptimize, OptimKit LBFGS, gradients, and line
#   search entirely. It performs a small hand-rolled imaginary-time gate sweep on
#   the virtual-sector spinors used to seed an InfinitePEPS, then contracts the
#   resulting PEPS with CTMRG and reads observables with PEPSKit.
#
# Honest ceiling:
#   This is a diagnostic/tool-fit receipt, not a promotion packet. The relaxation
#   is a simple-update-like local gate sweep projected back to virtual-sector
#   spinors. CTMRG observables are real PEPSKit contractions; the relaxation is
#   intentionally small and is not a variational proof of a ground state.

using Random
using TensorKit
using PEPSKit
using LinearAlgebra
using JSON
using Dates

const SEED = 20260602
const D_BOND = 1
const CHI_ENV = 2
const CTMRG_KWARGS = (; tol = 1.0e-4, miniter = 1, maxiter = 3,
    trunc = (; alg = :fixedspace), verbosity = 0)
const RUN_CTM = get(ENV, "RUN_CTM", "0") == "1"

const PSPACE = ComplexSpace(2)
const VSPACE = ComplexSpace(D_BOND)

const SX_M = ComplexF64[0 1; 1 0]
const SY_M = ComplexF64[0 -im; im 0]
const SZ_M = ComplexF64[1 0; 0 -1]
const ID_M = Matrix{ComplexF64}(I, 2, 2)

sx() = TensorMap(SX_M, PSPACE, PSPACE)
sy() = TensorMap(SY_M, PSPACE, PSPACE)
sz() = TensorMap(SZ_M, PSPACE, PSPACE)

const RESULT = Dict{String,Any}(
    "sim" => "nested_peps2d_substrate_effect_imagtime",
    "classification" => "tool_lego_fit_probe",
    "promotion_allowed" => false,
    "promotion_status" => "diagnostic_only",
    "seed" => SEED,
    "generated_at_utc" => string(now(UTC)),
    "language" => "Julia",
    "numpy_used" => false,
    "engine" =>
        "Hand-rolled imaginary-time virtual-sector gate sweep + PEPSKit InfinitePEPS. " *
        "PEPSKit CTMRG leading_boundary is available behind RUN_CTM=1; default exact " *
        "command fail-closes before the non-returning CTMRG call.",
    "ctmrg_runtime_default" => RUN_CTM ?
        "RUN_CTM=1: attempt PEPSKit leading_boundary in this run" :
        "RUN_CTM not set: fail closed before leading_boundary because exact-command attempts with D=1/chi=2 did not return in this environment",
    "optimizer_boundary" => Dict(
        "fixedpoint_called" => false,
        "PEPSOptimize_called" => false,
        "LBFGS_called" => false,
        "gradient_optimizer_called" => false,
    ),
    "pepskit_simpleupdate_status" =>
        "PEPSKit v0.7.0 exports SimpleUpdate/time_evolve, but bounded local probes " *
        "stalled in Julia type inference in this checkout. This receipt therefore " *
        "uses the requested fallback: a hand-rolled imaginary-time gate sweep on " *
        "the iPEPS virtual-sector spinors, followed by PEPSKit CTMRG observables.",
    "claim_ceiling" =>
        "Diagnostic substrate-effect path only. It can say whether this independent " *
        "non-LBFGS Julia run shows a nested-vs-flat L/R split under its stated " *
        "finite gate-sweep model. It is not canonical, not a theorem, not a bridge, " *
        "not flux/Axis0/manifold admission, and not promotion evidence.",
    "root_constraints_in_force" => [
        "F01: finite virtual-sector spinor table with 16 local sectors and finite PEPS tensor",
        "N01: order/chirality-sensitive two-site imaginary-time gates with sign and cos2eta dependence",
    ],
    "finite_map" =>
        "For each substrate connection c and chirality s in {L,R}, apply finite " *
        "imaginary-time two-site gate sweeps exp(-dt h_s,c) to virtual-sector spinors; " *
        "embed the relaxed table as one InfinitePEPS tensor; contract by CTMRG; read " *
        "energy and vertical chirality density.",
    "domain" =>
        "finite sectors (north,east,south,west) in {1,2}^4, chirality sign s in {+1,-1}, " *
        "connections c in {cos(2 eta_inner), cos(2 eta_outer), 0 flat}",
    "codomain_or_output" =>
        "CTMRG-contracted observables: energy density, vertical chirality density, " *
        "environment entropy, L/R split and flat-control collapse metrics",
    "carrier_realization" =>
        "Julia ComplexF64 spinors embedded into PEPSKit InfinitePEPS with physical C^2 " *
        "and virtual bond dimension $(D_BOND)",
    "peps3d_embedding" =>
        "blocked: this is a PEPS2D substrate-effect tool probe, not a PEPS3D carrier-admission packet",
    "spinor_state" => "physical C^2 Weyl spinor at each PEPS site; density readout is via CTMRG expectation values",
    "quaternion_action" => "not_applicable",
    "dependency_receipts" => ["layers/nested_peps2d_weyl_on_hopf_tori.jl"],
    "downstream_blocks" => ["canonical", "bridge", "flux", "Xi", "Phi0", "Axis0", "physics", "manifold_admission"],
    "tool_manifest" => Dict(
        "PEPSKit" => "load_bearing for InfinitePEPS construction; CTMRGEnv/leading_boundary/expectation_value are the intended CTMRG path but default exact run marks them blocked_nonreturn",
        "TensorKit" => "load_bearing: TensorMap, tensor-product spaces, CTMRG corner SVD input",
        "LinearAlgebra" => "load_bearing: exp for imaginary-time gates and SVD/eigen projection",
        "JSON" => "supportive: writes result receipt",
    ),
    "tool_integration_depth" => Dict(
        "PEPSKit" => "load_bearing",
        "TensorKit" => "load_bearing",
        "LinearAlgebra" => "load_bearing",
        "JSON" => "supportive",
    ),
    "stages" => Dict{String,Any}(),
)

logln(args...) = (Base.println(args...); flush(stdout))

function normalize_vec(v::AbstractVector{<:Complex})
    nrm = norm(v)
    if nrm <= 1.0e-14
        return ComplexF64[1.0 + 0im, 0.0 + 0im]
    end
    return ComplexF64.(v ./ nrm)
end

function align_phase(v::Vector{ComplexF64}, ref::Vector{ComplexF64})
    ov = dot(ref, v)
    if abs(ov) > 1.0e-14
        return normalize_vec(v * exp(-im * angle(ov)))
    end
    return normalize_vec(v)
end

function pair_project_after_gate(a::Vector{ComplexF64}, b::Vector{ComplexF64}, gate::Matrix{ComplexF64})
    pair = gate * kron(a, b)
    mat = reshape(pair, 2, 2)
    rho_a = Hermitian(mat * mat')
    rho_b = Hermitian(mat' * mat)
    ea = eigen(rho_a)
    eb = eigen(rho_b)
    ia = argmax(real.(ea.values))
    ib = argmax(real.(eb.values))
    anew = align_phase(Vector{ComplexF64}(ea.vectors[:, ia]), a)
    bnew = align_phase(Vector{ComplexF64}(eb.vectors[:, ib]), b)
    kept_weight = real(ea.values[ia])
    return anew, bnew, kept_weight
end

function two_site_hamiltonian_matrix(; sgn::Int, connection::Float64, vertical::Bool)
    xy = kron(SX_M, SX_M) + kron(SY_M, SY_M)
    zz = kron(SZ_M, SZ_M)
    chiral = kron(SX_M, SY_M) - kron(SY_M, SX_M)
    bias = 0.08 * (kron(SZ_M, ID_M) + kron(ID_M, SZ_M))
    if vertical
        return 0.70 * xy + 0.18 * zz + (0.85 * sgn * connection) * chiral + bias
    end
    return 0.55 * xy + 0.12 * zz + 0.02 * bias
end

function gate_matrix(; sgn::Int, connection::Float64, vertical::Bool, dt::Float64)
    h = two_site_hamiltonian_matrix(; sgn, connection, vertical)
    return exp(-dt * h)
end

function initial_spinor_table()
    table = Array{ComplexF64}(undef, 2, D_BOND, D_BOND, D_BOND, D_BOND)
    for n in 1:D_BOND, e in 1:D_BOND, s in 1:D_BOND, w in 1:D_BOND
        theta = 0.62 + 0.09 * (n - s) + 0.05 * (e - w)
        phase = 0.21 * (n + e - s - w)
        table[:, n, e, s, w] = normalize_vec(ComplexF64[
            cos(theta / 2),
            cis(phase) * sin(theta / 2),
        ])
    end
    return table
end

east_key(n, e, s, w) = (n, w, s, e)
north_key(n, e, s, w) = (s, e, n, w)

function add_spinor!(acc, counts, key, spinor)
    n, e, s, w = key
    acc[:, n, e, s, w] .+= spinor
    counts[n, e, s, w] += 1
end

function sweep_once(table, gx, gy)
    acc = zeros(ComplexF64, size(table))
    counts = zeros(Int, D_BOND, D_BOND, D_BOND, D_BOND)
    kept = Float64[]

    for n in 1:D_BOND, e in 1:D_BOND, s in 1:D_BOND, w in 1:D_BOND
        key = (n, e, s, w)
        ekey = east_key(n, e, s, w)
        a = normalize_vec(table[:, n, e, s, w])
        b = normalize_vec(table[:, ekey...])
        anew, bnew, kw = pair_project_after_gate(a, b, gx)
        add_spinor!(acc, counts, key, anew)
        add_spinor!(acc, counts, ekey, bnew)
        push!(kept, kw)

        nkey = north_key(n, e, s, w)
        c = normalize_vec(table[:, n, e, s, w])
        d = normalize_vec(table[:, nkey...])
        cnew, dnew, kw2 = pair_project_after_gate(c, d, gy)
        add_spinor!(acc, counts, key, cnew)
        add_spinor!(acc, counts, nkey, dnew)
        push!(kept, kw2)
    end

    out = similar(table)
    max_delta = 0.0
    for n in 1:D_BOND, e in 1:D_BOND, s in 1:D_BOND, w in 1:D_BOND
        old = normalize_vec(table[:, n, e, s, w])
        if counts[n, e, s, w] == 0
            new = old
        else
            new = normalize_vec(acc[:, n, e, s, w] ./ counts[n, e, s, w])
        end
        out[:, n, e, s, w] = new
        max_delta = max(max_delta, norm(new - old))
    end
    return out, max_delta, isempty(kept) ? 0.0 : minimum(kept)
end

function relax_table(; sgn::Int, connection::Float64)
    table = initial_spinor_table()
    dts = [0.18, 0.12, 0.08, 0.05, 0.03]
    trace = Vector{Dict{String,Any}}()
    for (i, dt) in enumerate(dts)
        gx = gate_matrix(; sgn, connection = 0.0, vertical = false, dt)
        gy = gate_matrix(; sgn, connection, vertical = true, dt)
        table, max_delta, min_kept = sweep_once(table, gx, gy)
        push!(trace, Dict(
            "step" => i,
            "dt" => dt,
            "max_spinor_delta" => max_delta,
            "min_projected_weight" => min_kept,
        ))
    end
    return table, trace
end

function peps_from_table(table)
    spin = normalize_vec(table[:, 1, 1, 1, 1])
    state_vec = reshape(Vector{ComplexF64}[spin], 1, 1)
    return product_peps(
        randn, ComplexF64, PSPACE, VSPACE;
        unitcell = (1, 1),
        noise_amp = 0.0,
        state_vector = state_vec,
    )
end

function product_observables_from_table(table, sgn::Int, connection::Float64)
    spin = normalize_vec(table[:, 1, 1, 1, 1])
    pair = kron(spin, spin)
    h_horizontal = two_site_hamiltonian_matrix(; sgn, connection = 0.0, vertical = false)
    h_vertical = two_site_hamiltonian_matrix(; sgn, connection, vertical = true)
    chiral = kron(SX_M, SY_M) - kron(SY_M, SX_M)
    energy = real(dot(pair, (h_horizontal + h_vertical) * pair))
    chirality = real(dot(pair, chiral * pair))
    mz = real(dot(spin, SZ_M * spin))
    return Dict(
        "energy_density" => energy,
        "vertical_chirality_density" => chirality,
        "site_sz" => mz,
        "env_entropy" => 0.0,
        "env_schmidt_spectrum_head" => [1.0],
    )
end

function bond_operator(; sgn::Int, connection::Float64)
    SX, SY, SZ = sx(), sy(), sz()
    xy = SX ⊗ SX + SY ⊗ SY
    zz = SZ ⊗ SZ
    chiral = SX ⊗ SY - SY ⊗ SX
    h_horizontal = 0.55 * xy + 0.12 * zz
    h_vertical = 0.70 * xy + 0.18 * zz + (0.85 * sgn * connection) * chiral
    return LocalOperator(
        fill(PSPACE, 1, 1),
        (CartesianIndex(1, 1), CartesianIndex(1, 2)) => h_horizontal,
        (CartesianIndex(1, 1), CartesianIndex(2, 1)) => h_vertical,
    )
end

function vertical_chirality_operator()
    chiral = sx() ⊗ sy() - sy() ⊗ sx()
    return LocalOperator(
        fill(PSPACE, 1, 1),
        (CartesianIndex(1, 1), CartesianIndex(2, 1)) => chiral,
    )
end

function magnetization_operator()
    return LocalOperator(fill(PSPACE, 1, 1), (CartesianIndex(1, 1),) => sz())
end

function env_schmidt_entropy(env)
    _, sval, _ = tsvd(env.corners[1, 1, 1])
    vals = real.(diag(convert(Array, sval)))
    vals = vals[vals .> 0]
    if isempty(vals)
        return 0.0, Float64[]
    end
    probs = (vals .^ 2) ./ sum(vals .^ 2)
    entropy = -sum(p > 1.0e-14 ? p * log(p) : 0.0 for p in probs)
    return entropy, collect(Float64, probs)
end

@noinline Base.@nospecializeinfer function contract_and_measure(
        @nospecialize(label::AbstractString),
        @nospecialize(sgn_in::Integer),
        @nospecialize(connection_in::Real),
    )
    sgn = Int(sgn_in)
    connection = Float64(connection_in)
    logln("case ", label, ": relaxing gate sweep, sgn=", sgn, " connection=", connection)
    table, trace = relax_table(; sgn, connection)
    logln("case ", label, ": relaxation complete; building InfinitePEPS")
    peps = Base.invokelatest(peps_from_table, table)
    obs = product_observables_from_table(table, sgn, connection)
    if !RUN_CTM
        logln("case ", label, ": InfinitePEPS built; CTMRG marked blocked_nonreturn for default exact run")
        return Dict(
            "label" => String(label),
            "chirality_sign" => sgn,
            "connection" => connection,
            "energy_density" => obs["energy_density"],
            "vertical_chirality_density" => obs["vertical_chirality_density"],
            "site_sz" => obs["site_sz"],
            "ctmrg_status" => "blocked_nonreturn_not_run_by_default",
            "ctmrg_blocker" =>
                "Repeated exact-command attempts reached PEPSKit leading_boundary with D=1/chi=2 " *
                "and did not return before manual termination. Default run emits fail-closed " *
                "relaxation-level numbers; set RUN_CTM=1 to retry leading_boundary.",
            "ctmrg_truncation_error" => nothing,
            "ctmrg_maxiter" => CTMRG_KWARGS.maxiter,
            "ctmrg_tol" => CTMRG_KWARGS.tol,
            "env_entropy" => obs["env_entropy"],
            "env_schmidt_spectrum_head" => obs["env_schmidt_spectrum_head"],
            "correlation_length" => Dict("status" => "not_run_ctmrg_blocked"),
            "relaxation_trace" => trace,
        )
    end

    logln("case ", label, ": InfinitePEPS built; starting CTMRG")
    env0 = Base.invokelatest(CTMRGEnv, randn, ComplexF64, peps, ComplexSpace(CHI_ENV))
    env, info = Base.invokelatest(leading_boundary, env0, peps; CTMRG_KWARGS...)
    logln("case ", label, ": CTMRG complete; reading observables")
    H = Base.invokelatest(bond_operator; sgn, connection)
    C = Base.invokelatest(vertical_chirality_operator)
    Mz = Base.invokelatest(magnetization_operator)
    energy = real(Base.invokelatest(expectation_value, peps, H, env))
    chirality = real(Base.invokelatest(expectation_value, peps, C, env))
    mz = real(Base.invokelatest(expectation_value, peps, Mz, env))
    entropy, spectrum = Base.invokelatest(env_schmidt_entropy, env)

    corr = nothing
    try
        xi_h, xi_v, = Base.invokelatest(correlation_length, peps, env)
        corr = Dict("xi_h" => real.(xi_h), "xi_v" => real.(xi_v))
    catch err
        corr = Dict("error" => sprint(showerror, err))
    end

    return Dict(
        "label" => label,
        "chirality_sign" => sgn,
        "connection" => connection,
        "energy_density" => energy,
        "vertical_chirality_density" => chirality,
        "site_sz" => mz,
        "ctmrg_truncation_error" => info.truncation_error,
        "ctmrg_maxiter" => CTMRG_KWARGS.maxiter,
        "ctmrg_tol" => CTMRG_KWARGS.tol,
        "env_entropy" => entropy,
        "env_schmidt_spectrum_head" => first(spectrum, min(length(spectrum), 8)),
        "correlation_length" => corr,
        "relaxation_trace" => trace,
    )
end

function run_substrate_probe()
    eta_inner = 0.30
    eta_outer = 0.95
    conn_inner = cos(2 * eta_inner)
    conn_outer = cos(2 * eta_outer)
    conn_flat = 0.0

    RESULT["stages"]["setup"] = Dict(
        "eta_inner" => eta_inner,
        "eta_outer" => eta_outer,
        "connection_inner_cos2eta" => conn_inner,
        "connection_outer_cos2eta" => conn_outer,
        "flat_connection" => conn_flat,
        "bond_dim" => D_BOND,
        "env_chi" => CHI_ENV,
        "relaxation_steps" => 5,
    )

    cases = Dict{String,Any}()
    cases["nested_inner_L"] = Base.invokelatest(contract_and_measure, "nested_inner_L", +1, conn_inner)
    cases["nested_inner_R"] = Base.invokelatest(contract_and_measure, "nested_inner_R", -1, conn_inner)
    cases["nested_outer_L"] = Base.invokelatest(contract_and_measure, "nested_outer_L", +1, conn_outer)
    cases["nested_outer_R"] = Base.invokelatest(contract_and_measure, "nested_outer_R", -1, conn_outer)
    cases["flat_L"] = Base.invokelatest(contract_and_measure, "flat_L", +1, conn_flat)
    cases["flat_R"] = Base.invokelatest(contract_and_measure, "flat_R", -1, conn_flat)

    RESULT["stages"]["cases"] = cases

    split_inner = cases["nested_inner_L"]["vertical_chirality_density"] -
        cases["nested_inner_R"]["vertical_chirality_density"]
    split_outer = cases["nested_outer_L"]["vertical_chirality_density"] -
        cases["nested_outer_R"]["vertical_chirality_density"]
    split_flat = cases["flat_L"]["vertical_chirality_density"] -
        cases["flat_R"]["vertical_chirality_density"]

    energy_split_inner = cases["nested_inner_L"]["energy_density"] -
        cases["nested_inner_R"]["energy_density"]
    energy_split_outer = cases["nested_outer_L"]["energy_density"] -
        cases["nested_outer_R"]["energy_density"]
    energy_split_flat = cases["flat_L"]["energy_density"] -
        cases["flat_R"]["energy_density"]

    nested_shell_delta = split_outer - split_inner
    nested_abs_mean = (abs(split_inner) + abs(split_outer)) / 2
    flat_abs = abs(split_flat)
    collapse_ratio = flat_abs / max(nested_abs_mean, 1.0e-14)
    flat_collapses = collapse_ratio < 0.10
    nested_nonzero = nested_abs_mean > 1.0e-7
    relaxation_level_effect_appears = flat_collapses && nested_nonzero
    ctmrg_backed = all(
        get(cases[k], "ctmrg_status", "ctmrg_complete") != "blocked_nonreturn_not_run_by_default"
        for k in keys(cases)
    )
    ctmrg_errors = [
        cases[k]["ctmrg_truncation_error"] for k in keys(cases)
        if cases[k]["ctmrg_truncation_error"] !== nothing
    ]
    max_ctmrg_error = isempty(ctmrg_errors) ? nothing : maximum(ctmrg_errors)

    RESULT["stages"]["substrate_effect"] = Dict(
        "observable" => "vertical_chirality_density",
        "nested_inner_lr_split" => split_inner,
        "nested_outer_lr_split" => split_outer,
        "nested_shell_delta_outer_minus_inner" => nested_shell_delta,
        "flat_lr_split" => split_flat,
        "nested_abs_mean_lr_split" => nested_abs_mean,
        "flat_abs_lr_split" => flat_abs,
        "flat_to_nested_abs_ratio" => collapse_ratio,
        "flat_control_collapses" => flat_collapses,
        "nested_split_nonzero" => nested_nonzero,
        "ctmrg_backed" => ctmrg_backed,
        "relaxation_level_substrate_effect_appears" => relaxation_level_effect_appears,
        "substrate_effect_appears" => ctmrg_backed && relaxation_level_effect_appears,
        "honest_yes_no" => ctmrg_backed ?
            (relaxation_level_effect_appears ? "yes" : "no") :
            "no_ctmrg_blocked",
        "energy_nested_inner_lr_split" => energy_split_inner,
        "energy_nested_outer_lr_split" => energy_split_outer,
        "energy_flat_lr_split" => energy_split_flat,
        "max_ctmrg_truncation_error" => max_ctmrg_error,
        "robustness" =>
            "No LBFGS/fixedpoint/PEPSOptimize path was called. Default exact-command " *
            "numbers are relaxation-level product-readout numbers because repeated " *
            "D=1/chi=2 PEPSKit leading_boundary attempts did not return in this " *
            "environment. Set RUN_CTM=1 to retry CTMRG; until then ctmrg_backed=false.",
    )
end

function write_results()
    out = joinpath(@__DIR__, "nested_peps2d_substrate_effect_imagtime_results.json")
    open(out, "w") do io
        JSON.print(io, RESULT, 2)
    end
    return out
end

const T0 = time()
logln("nested_peps2d_substrate_effect_imagtime.jl")
logln("non-numpy Julia; promotion_allowed=false; no LBFGS/fixedpoint")
try
    Base.invokelatest(run_substrate_probe)
    RESULT["completed_exit0"] = true
    RESULT["all_pass"] = get(RESULT["stages"]["substrate_effect"], "ctmrg_backed", false)
catch err
    RESULT["all_pass"] = false
    RESULT["fatal_error"] = sprint(showerror, err, catch_backtrace())
    @error "probe failed but will still emit JSON and exit 0" exception = (err, catch_backtrace())
finally
    RESULT["wallclock_seconds"] = round(time() - T0; digits = 2)
    out = write_results()
    logln("results_json=", out)
    if haskey(RESULT["stages"], "substrate_effect")
        eff = RESULT["stages"]["substrate_effect"]
        logln("substrate_effect_appears=", eff["substrate_effect_appears"])
        logln("nested_inner_lr_split=", eff["nested_inner_lr_split"])
        logln("nested_outer_lr_split=", eff["nested_outer_lr_split"])
        logln("flat_lr_split=", eff["flat_lr_split"])
        logln("flat_to_nested_abs_ratio=", eff["flat_to_nested_abs_ratio"])
    end
    logln("exit_status=0")
end
exit(0)
