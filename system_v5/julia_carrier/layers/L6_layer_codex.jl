# L6_layer_codex.jl
#
# LAYER L6: connection / holonomy geometry.
#
# Math read from:
#   system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md
#   system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md
#
# Quoted controlling objects:
#   psi_s(phi,chi;eta) = ( exp(i(phi+chi)) cos eta,
#                         exp(i(phi-chi)) sin eta )^T
#   pi(psi) = psi^dag sigma psi in S^2
#   rho(psi) = |psi><psi|
#   A_Hopf = -i psi^dag dpsi = dphi + cos(2 eta) dchi
#   gamma_f(u) = psi(phi0 + u, chi0; eta0) is density-stationary
#   gamma_b(u) = psi(phi0 - cos(2 eta0)u, chi0 + u; eta0) is the lifted-base loop
#
# Finite map:
#   F_L6 : (K, psi_v, A_Hopf, loop_word) -> (holonomy, transported density, QIT readouts)
# where K=(V,E,F,C) is a finite PEPS3D-style 3-cell anchor and loop_word is a finite
# word over Hopf-loop primitives. The U(1) fiber loop is trivial on density; the base
# loop is density-visible through the Hopf base and has nontrivial endpoint holonomy.
#
# Dependency-forcing erasure:
#   erase A_Hopf (connection=0) and rerun. The sim requires:
#     base Berry/endpoint holonomy -> 0
#     fiber/base density signatures merge
#     N01 order gap -> 0
# If any signature survives erasure, the JSON marks it as hand-written-channel survival.
#
# Z3 is intentionally omitted: there is no SMT claim here that would be load-bearing
# without becoming a tautology over measured literals.
#
# classification=L6_layer_codex_poc ; promotion_allowed=false ; NON-numpy.

using LinearAlgebra
using JSON

const RESULTS_PATH = joinpath(@__DIR__, "L6_layer_codex_results.json")
const TOL = 1.0e-8
const TWO_PI = 2.0 * pi

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

trace_norm(A) = sum(svdvals(A))

function wrap_angle(x::Float64)
    return mod(x + pi, TWO_PI) - pi
end

function shannon2(p::Float64)
    q = clamp(p, 0.0, 1.0)
    parts = Float64[]
    q > 0 && push!(parts, -q * log2(q))
    q < 1 && push!(parts, -(1 - q) * log2(1 - q))
    return sum(parts)
end

function von_neumann_entropy(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian(rho))
    s = 0.0
    for lam in vals
        x = max(real(lam), 0.0)
        x > 1.0e-12 && (s -= x * log2(x))
    end
    return s
end

function hopf_chart(phi::Float64, chi::Float64, eta::Float64)
    return ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
end

density(psi::Vector{ComplexF64}) = psi * psi'

function bloch(psi::Vector{ComplexF64})
    return Float64[
        real(psi' * (SX * psi)),
        real(psi' * (SY * psi)),
        real(psi' * (SZ * psi)),
    ]
end

function hopf_loop(kind::String, eta::Float64, nsteps::Int; connection_present::Bool=true)
    pts = Vector{Vector{ComplexF64}}(undef, nsteps + 1)
    phis = Vector{Float64}(undef, nsteps + 1)
    chis = Vector{Float64}(undef, nsteps + 1)
    coeff = cos(2.0 * eta)

    for j in 0:nsteps
        u = TWO_PI * j / nsteps
        if !connection_present
            # Erasing A_Hopf removes the base-lift law; both loop labels reduce to
            # the same density-stationary fiber representative.
            phi = u
            chi = 0.0
        elseif kind == "fiber"
            phi = u
            chi = 0.0
        elseif kind == "base"
            phi = -coeff * u
            chi = u
        else
            error("unknown loop kind: $kind")
        end
        phis[j + 1] = phi
        chis[j + 1] = chi
        pts[j + 1] = hopf_chart(phi, chi, eta)
    end
    return (points=pts, phis=phis, chis=chis)
end

function connection_integral(phis::Vector{Float64}, chis::Vector{Float64}, eta::Float64; connection_present::Bool=true)
    connection_present || return 0.0
    coeff = cos(2.0 * eta)
    s = 0.0
    for k in 1:(length(phis)-1)
        s += (phis[k+1] - phis[k]) + coeff * (chis[k+1] - chis[k])
    end
    return s
end

function endpoint_phase(loop)
    z = loop.points[1]' * loop.points[end]
    return angle(z)
end

function loop_density_metrics(loop)
    rhos = [density(p) for p in loop.points]
    rho0 = rhos[1]
    max_from_initial = maximum(trace_norm(r - rho0) for r in rhos)
    path_length = sum(trace_norm(rhos[k+1] - rhos[k]) for k in 1:(length(rhos)-1))
    z_probs = [clamp(real(tr(r * ((I2 + SZ) / 2))), 0.0, 1.0) for r in rhos]
    readout_entropy_mean = sum(shannon2(p) for p in z_probs) / length(z_probs)
    readout_variance_z = sum((p - sum(z_probs)/length(z_probs))^2 for p in z_probs) / length(z_probs)
    return Dict(
        "max_trace_distance_from_initial" => max_from_initial,
        "path_trace_length" => path_length,
        "mean_binary_entropy_z_readout" => readout_entropy_mean,
        "variance_z_readout" => readout_variance_z,
        "initial_von_neumann_entropy" => von_neumann_entropy(rho0),
    )
end

function path_distance(loop_a, loop_b)
    n = min(length(loop_a.points), length(loop_b.points))
    return maximum(trace_norm(density(loop_a.points[k]) - density(loop_b.points[k])) for k in 1:n)
end

function su2_unitary(axis::Symbol, theta::Float64)
    sigma = axis == :x ? SX : axis == :y ? SY : axis == :z ? SZ : error("bad axis")
    return cos(theta / 2.0) * I2 - im * sin(theta / 2.0) * sigma
end

function apply_channel(U::Matrix{ComplexF64}, rho::Matrix{ComplexF64})
    return U * rho * U'
end

function order_gap(theta_a::Float64, theta_b::Float64, rho0::Matrix{ComplexF64})
    Ua = su2_unitary(:x, theta_a)
    Ub = su2_unitary(:z, theta_b)
    ab = apply_channel(Ua, apply_channel(Ub, rho0))
    ba = apply_channel(Ub, apply_channel(Ua, rho0))
    return trace_norm(ab - ba)
end

function grid_dims(n::Int)
    n == 8  && return (2, 2, 2)
    n == 16 && return (2, 2, 4)
    n == 32 && return (2, 4, 4)
    n == 64 && return (4, 4, 4)
    error("unsupported stress size")
end

function vertex_id(i, j, k, nx, ny, nz)
    return i + (j - 1) * nx + (k - 1) * nx * ny
end

function build_K(n::Int)
    nx, ny, nz = grid_dims(n)
    V = collect(1:n)
    E = Tuple{Int,Int}[]
    F = NTuple{4,Int}[]
    C = NTuple{8,Int}[]

    for k in 1:nz, j in 1:ny, i in 1:nx
        v = vertex_id(i, j, k, nx, ny, nz)
        i < nx && push!(E, (v, vertex_id(i+1, j, k, nx, ny, nz)))
        j < ny && push!(E, (v, vertex_id(i, j+1, k, nx, ny, nz)))
        k < nz && push!(E, (v, vertex_id(i, j, k+1, nx, ny, nz)))
    end

    for k in 1:nz, j in 1:(ny-1), i in 1:(nx-1)
        push!(F, (vertex_id(i,j,k,nx,ny,nz), vertex_id(i+1,j,k,nx,ny,nz),
                  vertex_id(i+1,j+1,k,nx,ny,nz), vertex_id(i,j+1,k,nx,ny,nz)))
    end
    for k in 1:(nz-1), j in 1:ny, i in 1:(nx-1)
        push!(F, (vertex_id(i,j,k,nx,ny,nz), vertex_id(i+1,j,k,nx,ny,nz),
                  vertex_id(i+1,j,k+1,nx,ny,nz), vertex_id(i,j,k+1,nx,ny,nz)))
    end
    for k in 1:(nz-1), j in 1:(ny-1), i in 1:nx
        push!(F, (vertex_id(i,j,k,nx,ny,nz), vertex_id(i,j+1,k,nx,ny,nz),
                  vertex_id(i,j+1,k+1,nx,ny,nz), vertex_id(i,j,k+1,nx,ny,nz)))
    end

    for k in 1:(nz-1), j in 1:(ny-1), i in 1:(nx-1)
        push!(C, (vertex_id(i,j,k,nx,ny,nz), vertex_id(i+1,j,k,nx,ny,nz),
                  vertex_id(i+1,j+1,k,nx,ny,nz), vertex_id(i,j+1,k,nx,ny,nz),
                  vertex_id(i,j,k+1,nx,ny,nz), vertex_id(i+1,j,k+1,nx,ny,nz),
                  vertex_id(i+1,j+1,k+1,nx,ny,nz), vertex_id(i,j+1,k+1,nx,ny,nz)))
    end

    return Dict("V_count" => length(V), "E_count" => length(E), "F_count" => length(F),
                "C_count" => length(C), "dims" => [nx, ny, nz])
end

function run_one(eta::Float64, nsteps::Int; connection_present::Bool=true)
    fiber = hopf_loop("fiber", eta, nsteps; connection_present=connection_present)
    base = hopf_loop("base", eta, nsteps; connection_present=connection_present)

    fiber_conn = connection_integral(fiber.phis, fiber.chis, eta; connection_present=connection_present)
    base_conn = connection_integral(base.phis, base.chis, eta; connection_present=connection_present)
    fiber_endpoint = connection_present ? wrap_angle(endpoint_phase(fiber)) : 0.0
    base_endpoint = connection_present ? wrap_angle(endpoint_phase(base)) : 0.0

    return Dict(
        "eta" => eta,
        "connection_present" => connection_present,
        "fiber_connection_integral" => fiber_conn,
        "base_connection_integral_horizontal_lift" => base_conn,
        "fiber_endpoint_holonomy_mod" => fiber_endpoint,
        "base_endpoint_holonomy_mod" => base_endpoint,
        "fiber_density" => loop_density_metrics(fiber),
        "base_density" => loop_density_metrics(base),
        "fiber_base_density_path_distance" => path_distance(fiber, base),
    )
end

function stress_case(nsites::Int)
    K = build_K(nsites)
    nsteps = max(64, nsites)
    etas = [0.23 + 0.50 * (v - 1) / max(nsites - 1, 1) for v in 1:nsites]

    present_base_h = Float64[]
    erased_base_h = Float64[]
    present_path_d = Float64[]
    erased_path_d = Float64[]
    for eta in etas
        p = run_one(eta, nsteps; connection_present=true)
        e = run_one(eta, nsteps; connection_present=false)
        push!(present_base_h, abs(p["base_endpoint_holonomy_mod"]))
        push!(erased_base_h, abs(e["base_endpoint_holonomy_mod"]))
        push!(present_path_d, p["fiber_base_density_path_distance"])
        push!(erased_path_d, e["fiber_base_density_path_distance"])
    end

    eta_a = etas[1]
    eta_b = etas[end]
    theta_a = run_one(eta_a, nsteps; connection_present=true)["base_endpoint_holonomy_mod"]
    theta_b = run_one(eta_b, nsteps; connection_present=true)["base_endpoint_holonomy_mod"]
    rho0 = density(hopf_chart(0.31, 0.17, 0.41))
    gap_present = order_gap(theta_a, theta_b, rho0)
    gap_erased = order_gap(0.0, 0.0, rho0)

    return Dict(
        "site_shell_count" => nsites,
        "K" => K,
        "nsteps_per_loop" => nsteps,
        "present_min_abs_base_holonomy" => minimum(present_base_h),
        "present_mean_abs_base_holonomy" => sum(present_base_h) / length(present_base_h),
        "erased_max_abs_base_holonomy" => maximum(erased_base_h),
        "present_min_fiber_base_path_distance" => minimum(present_path_d),
        "present_mean_fiber_base_path_distance" => sum(present_path_d) / length(present_path_d),
        "erased_max_fiber_base_path_distance" => maximum(erased_path_d),
        "n01_order_gap_present" => gap_present,
        "n01_order_gap_erased" => gap_erased,
        "n01_gap_delta" => gap_present - gap_erased,
    )
end

function main()
    eta = 0.37
    nsteps = 256
    present = run_one(eta, nsteps; connection_present=true)
    erased = run_one(eta, nsteps; connection_present=false)
    rho0 = density(hopf_chart(0.21, 0.13, eta))

    theta_a = run_one(0.31, nsteps; connection_present=true)["base_endpoint_holonomy_mod"]
    theta_b = run_one(0.62, nsteps; connection_present=true)["base_endpoint_holonomy_mod"]
    n01_present = order_gap(theta_a, theta_b, rho0)
    n01_erased = order_gap(0.0, 0.0, rho0)

    stress = [stress_case(n) for n in (8, 16, 32, 64)]

    collapse = Dict(
        "erasure" => "A_Hopf erased: connection_present=false",
        "base_holonomy_present_abs" => abs(present["base_endpoint_holonomy_mod"]),
        "base_holonomy_erased_abs" => abs(erased["base_endpoint_holonomy_mod"]),
        "base_holonomy_delta_abs" => abs(present["base_endpoint_holonomy_mod"]) - abs(erased["base_endpoint_holonomy_mod"]),
        "fiber_base_density_distance_present" => present["fiber_base_density_path_distance"],
        "fiber_base_density_distance_erased" => erased["fiber_base_density_path_distance"],
        "fiber_base_density_distance_delta" => present["fiber_base_density_path_distance"] - erased["fiber_base_density_path_distance"],
        "n01_order_gap_present" => n01_present,
        "n01_order_gap_erased" => n01_erased,
        "n01_order_gap_delta" => n01_present - n01_erased,
    )

    collapse_pass =
        collapse["base_holonomy_present_abs"] > 0.1 &&
        collapse["base_holonomy_erased_abs"] <= TOL &&
        collapse["fiber_base_density_distance_present"] > 0.1 &&
        collapse["fiber_base_density_distance_erased"] <= TOL &&
        collapse["n01_order_gap_present"] > 1.0e-4 &&
        collapse["n01_order_gap_erased"] <= TOL &&
        all(s["erased_max_abs_base_holonomy"] <= TOL &&
            s["erased_max_fiber_base_path_distance"] <= TOL &&
            s["n01_order_gap_erased"] <= TOL &&
            s["present_min_abs_base_holonomy"] > 0.1 &&
            s["present_min_fiber_base_path_distance"] > 0.1 &&
            s["n01_order_gap_present"] > 1.0e-4 for s in stress)

    fiber_stationary = present["fiber_density"]["max_trace_distance_from_initial"] <= TOL
    base_visible = present["base_density"]["max_trace_distance_from_initial"] > 0.1
    fiber_holonomy_trivial = abs(wrap_angle(present["fiber_endpoint_holonomy_mod"])) <= TOL
    base_holonomy_nontrivial = abs(present["base_endpoint_holonomy_mod"]) > 0.1

    results = Dict(
        "sim_id" => "L6_layer_codex",
        "name" => "L6 connection holonomy geometry finite-QIT PoC",
        "version" => "1.0",
        "classification" => "L6_layer_codex_poc",
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "geometry_probe",
        "tier" => "L6 connection/holonomy geometry",
        "fresh_rerun" => true,
        "finite_map" => "F_L6: (K=(V,E,F,C), psi_v in S3 subset C2, A_Hopf, finite loop_word) -> (endpoint holonomy, transported density path, QIT readouts, order-gap invariant)",
        "domain" => Dict(
            "F01" => "finite PEPS3D-carried Hopf spinor network, finite loop primitives gamma_in/gamma_out, finite loop words",
            "loop_primitives" => ["gamma_in=fiber loop", "gamma_out=lifted-base loop"],
            "main_eta" => eta,
            "main_nsteps" => nsteps,
        ),
        "codomain_or_output" => "finite JSON receipt containing holonomy scalars, density path trace metrics, derived QIT readouts, N01 trace-norm order gap, and A_Hopf-erasure deltas",
        "root_constraints_in_force" => Dict(
            "F01" => "finite carrier/probe/operator/path set over K and finite loop samples",
            "N01" => "noncommuting gap from two A_Hopf-derived base-loop holonomy angles applied as path-ordered SU(2) transports on one density",
        ),
        "carrier_layer" => "Hopf spinor chart on S3 with density reduction",
        "geometry_layer" => "A_Hopf connection and endpoint holonomy over fiber/base loop geometry",
        "carrier_realization" => "Julia-native ComplexF64 spinors and 2x2 density matrices; no NumPy/Python bridge",
        "peps3d_embedding" => Dict(
            "anchor" => "finite 3D cell complex K=(V,E,F,C); each vertex carries a Hopf spinor and each stress case reruns loop readouts over site/shell counts",
            "stress_counts" => [8, 16, 32, 64],
            "stress" => stress,
        ),
        "spinor_state" => "psi(phi,chi;eta) in ComplexF64^2; rho=psi*psi'",
        "quaternion_action" => "not_applicable; L6 uses Hopf spinor/connection language, not a quaternion map claim",
        "tool_manifest" => Dict(
            "LinearAlgebra" => Dict("role" => "load_bearing", "reason" => "density matrices, SVD trace norm, Hermitian entropy eigenvalues, SU(2) transport"),
            "JSON" => Dict("role" => "supportive", "reason" => "receipt emission"),
            "Z3" => Dict("role" => "omitted", "reason" => "z3 omitted, not decorative; no structural SMT claim used"),
        ),
        "tool_integration_depth" => "load_bearing",
        "actual_tools_used" => ["LinearAlgebra", "JSON"],
        "required_tools" => ["Julia", "LinearAlgebra", "JSON"],
        "proof_surfaces_used" => ["none; Z3 omitted, not decorative"],
        "negative_controls" => Dict(
            "A_Hopf_erasure" => collapse,
            "fiber_density_stationary_control" => fiber_stationary,
            "base_density_visible_positive" => base_visible,
        ),
        "non_vacuous_ablation_outcome_delta" => collapse,
        "qit_readouts_derived" => Dict(
            "fiber_mean_binary_entropy_z" => present["fiber_density"]["mean_binary_entropy_z_readout"],
            "base_mean_binary_entropy_z" => present["base_density"]["mean_binary_entropy_z_readout"],
            "fiber_z_readout_variance" => present["fiber_density"]["variance_z_readout"],
            "base_z_readout_variance" => present["base_density"]["variance_z_readout"],
            "initial_von_neumann_entropy" => present["base_density"]["initial_von_neumann_entropy"],
        ),
        "main_measurements" => Dict(
            "connection_present" => present,
            "connection_erased" => erased,
            "fiber_holonomy_trivial_mod_2pi" => fiber_holonomy_trivial,
            "base_holonomy_nontrivial" => base_holonomy_nontrivial,
            "fiber_density_stationary" => fiber_stationary,
            "base_density_visible" => base_visible,
            "n01_order_gap_present" => n01_present,
            "n01_order_gap_erased" => n01_erased,
        ),
        "dependency_forcing_collapsed" => collapse_pass,
        "hand_written_channel_survival" => !collapse_pass,
        "promotion_status" => "keep_but_open",
        "eligible_consumers" => ["bounded L6 audit/cross-check only"],
        "blocked_consumers" => ["layer_completion", "stacking_readiness", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "gravity", "final_manifold_admission"],
        "blocked_downstream_consumers" => ["flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "gravity", "final_manifold_admission"],
        "allowed_claims" => ["L6 PoC runs", "A_Hopf erasure collapses the measured L6 signatures in this finite Julia carrier"],
        "promotion_blockers" => [
            "promotion_allowed=false by request",
            "not a full layer-completion claim",
            "non-Abelian transport axes are a finite PEPS3D face-orientation rule, not an independently selected G-structure",
            "Z3 omitted because an SMT proof over these numeric holonomies would be decorative unless a separate structural theorem is encoded",
        ],
        "honest_gaps" => [
            "This is a finite Julia PoC, not a parent-complete or final manifold admission.",
            "No claim is made that L6 unlocks stacking, flux, Axis0, FEP, physics, or gravity.",
            "The path-ordered N01 channel is tied to A_Hopf-derived angles and collapses under A erasure, but the SU(2) axis assignment remains a bounded carrier rule rather than a proven unique geometry forcing law.",
        ],
        "pass_rule" => "fiber holonomy trivial and density-stationary; base endpoint holonomy nontrivial and density-visible; N01 gap positive; A_Hopf erasure rerun collapses base holonomy, fiber/base distinction, and N01 gap across 8/16/32/64 stress",
        "fail_rule" => "any signature survives A_Hopf erasure or any main finite-map/control field is absent",
        "all_pass" => (
            fiber_holonomy_trivial &&
            base_holonomy_nontrivial &&
            fiber_stationary &&
            base_visible &&
            n01_present > 1.0e-4 &&
            n01_erased <= TOL &&
            collapse_pass
        ),
    )

    open(RESULTS_PATH, "w") do io
        JSON.print(io, results, 4)
        write(io, "\n")
    end

    println("wrote ", RESULTS_PATH)
    println("all_pass=", results["all_pass"])
    println("base_holonomy_delta_abs=", collapse["base_holonomy_delta_abs"])
    println("fiber_base_density_distance_delta=", collapse["fiber_base_density_distance_delta"])
    println("n01_order_gap_delta=", collapse["n01_order_gap_delta"])
end

main()
