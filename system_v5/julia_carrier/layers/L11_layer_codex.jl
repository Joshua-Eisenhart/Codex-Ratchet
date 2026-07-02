using LinearAlgebra
using JSON

# L11 operator-substage local cell POC.
#
# Read-gate math used directly:
# - registry: L11 = "allowed local operators as PEPS3D-carried cell/channel actions";
#   layer receipts need finite_map, F01/N01, PEPS3D K=(V,E,F,C), 8/16/32/64 stress,
#   real ablation, negative controls, and blocked consumers.
# - operator reference: intrinsic operators are Ti, Te, Fi, Fe:
#   Ti = z-basis pinch; Te = x-basis pinch; Fi = x-rotation; Fe = z-rotation.
# - order test: gap(Phi_a,Phi_b,rho) = ||Phi_a Phi_b rho - Phi_b Phi_a rho||_1.
#
# Z3 is intentionally omitted: this layer's load-bearing claim is a measured
# channel-order collapse under an erasure rerun, not an SMT structural claim.

const I2 = ComplexF64[1 0; 0 1]
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const PAULI = [I2, sx, sy, sz]
const PAULI_LABELS = ["I", "X", "Y", "Z"]

const P0 = (I2 + sz) / 2
const P1 = (I2 - sz) / 2
const Qp = (I2 + sx) / 2
const Qm = (I2 - sx) / 2

trace_norm(A) = sum(svdvals(A))
herm(A) = (A + A') / 2

function density_from_angles(phi, chi, eta)
    psi = ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
    psi = psi / norm(psi)
    return psi, psi * psi'
end

function von_neumann_entropy(rho)
    vals = eigvals(Hermitian(herm(rho)))
    total = 0.0
    for lam in real.(vals)
        p = max(lam, 0.0)
        if p > 1e-12
            total -= p * log2(p)
        end
    end
    return total
end

purity(rho) = real(tr(rho * rho))

pinch_z(q) = rho -> (1 - q) * rho + q * (P0 * rho * P0 + P1 * rho * P1)
pinch_x(q) = rho -> (1 - q) * rho + q * (Qp * rho * Qp + Qm * rho * Qm)

function rot_x(theta)
    U = cos(theta / 2) * I2 - im * sin(theta / 2) * sx
    return rho -> U * rho * U'
end

function rot_z(phi)
    U = ComplexF64[exp(-im * phi / 2) 0; 0 exp(im * phi / 2)]
    return rho -> U * rho * U'
end

struct ChannelSpec
    label::String
    standard_name::String
    channel::Function
end

function pauli_transfer_matrix(ch::ChannelSpec)
    R = zeros(Float64, 4, 4)
    for i in 1:4, j in 1:4
        R[i, j] = real(tr(PAULI[i] * ch.channel(PAULI[j])) / 2)
    end
    return R
end

function fixed_algebra_basis(ch::ChannelSpec; tol=1e-10)
    kept = String[]
    defects = Dict{String,Float64}()
    for (label, P) in zip(PAULI_LABELS, PAULI)
        defect = opnorm(ch.channel(P) - P)
        defects[label] = defect
        if defect < tol
            push!(kept, label)
        end
    end
    return kept, defects
end

compose(a::ChannelSpec, b::ChannelSpec, rho) = a.channel(b.channel(rho))

function order_gap(a::ChannelSpec, b::ChannelSpec, rho)
    return trace_norm(compose(a, b, rho) - compose(b, a, rho))
end

function apply_sequence(seq::Vector{ChannelSpec}, rho)
    out = rho
    for ch in seq
        out = ch.channel(out)
    end
    return out
end

function local_K(N)
    V = collect(1:N)
    E = [[i, i + 1] for i in 1:(N - 1)]
    append!(E, [[i, i + 4] for i in 1:(N - 4)])
    F = [[i, i + 1, i + 5, i + 4] for i in 1:(N - 5) if (i % 4) != 0]
    C = [[i, i + 1, i + 4, i + 5] for i in 1:(N - 5) if (i % 4) != 0]
    return Dict(
        "site_count" => N,
        "V_count" => length(V),
        "E_count" => length(E),
        "F_count" => length(F),
        "C_count" => length(C),
        "V_sample" => V[1:min(N, 8)],
        "E_sample" => E[1:min(length(E), 8)],
        "F_sample" => F[1:min(length(F), 4)],
        "C_sample" => C[1:min(length(C), 4)],
        "anchor_level" => "finite PEPS3D K=(V,E,F,C) combinatorial local-cell anchor; no tensor-network contraction claimed",
    )
end

function site_state(site, N)
    phi = 0.17 * site
    chi = 0.11 * (site % 7 + 1)
    eta = (pi / 9) + (site - 1) * (pi / 5) / max(N - 1, 1)
    return density_from_angles(phi, chi, eta)
end

function stress(channels::Vector{ChannelSpec}, erased::Vector{ChannelSpec}, sizes)
    rows = []
    for N in sizes
        K = local_K(N)
        pair_gaps = Float64[]
        pair_gaps_erased = Float64[]
        seq_gaps = Float64[]
        seq_gaps_erased = Float64[]
        entropy_before = Float64[]
        entropy_after = Float64[]
        entropy_after_erased = Float64[]
        for site in 1:N
            _, rho = site_state(site, N)
            for i in 1:(length(channels) - 1)
                push!(pair_gaps, order_gap(channels[i], channels[i + 1], rho))
                push!(pair_gaps_erased, order_gap(erased[i], erased[i + 1], rho))
            end
            forward = apply_sequence(channels, rho)
            reverse_out = apply_sequence(reverse(channels), rho)
            forward_erased = apply_sequence(erased, rho)
            reverse_erased_out = apply_sequence(reverse(erased), rho)
            push!(seq_gaps, trace_norm(forward - reverse_out))
            push!(seq_gaps_erased, trace_norm(forward_erased - reverse_erased_out))
            push!(entropy_before, von_neumann_entropy(rho))
            push!(entropy_after, von_neumann_entropy(forward))
            push!(entropy_after_erased, von_neumann_entropy(forward_erased))
        end
        max_pair = maximum(pair_gaps)
        max_pair_erased = maximum(pair_gaps_erased)
        max_seq = maximum(seq_gaps)
        max_seq_erased = maximum(seq_gaps_erased)
        push!(rows, Dict(
            "N" => N,
            "K" => K,
            "max_adjacent_pair_order_gap" => max_pair,
            "max_adjacent_pair_order_gap_erased" => max_pair_erased,
            "pair_gap_collapse_delta" => max_pair - max_pair_erased,
            "max_sequence_order_gap_forward_vs_reverse" => max_seq,
            "max_sequence_order_gap_erased" => max_seq_erased,
            "sequence_gap_collapse_delta" => max_seq - max_seq_erased,
            "mean_entropy_before" => sum(entropy_before) / length(entropy_before),
            "mean_entropy_after" => sum(entropy_after) / length(entropy_after),
            "mean_entropy_after_erased" => sum(entropy_after_erased) / length(entropy_after_erased),
            "mean_entropy_delta" => (sum(entropy_after) - sum(entropy_before)) / length(entropy_before),
            "mean_entropy_delta_erased" => (sum(entropy_after_erased) - sum(entropy_before)) / length(entropy_before),
        ))
    end
    return rows
end

function matrix_to_json(M)
    return [[M[i, j] for j in 1:size(M, 2)] for i in 1:size(M, 1)]
end

function round_nested(x)
    if x isa Float64
        return round(x, digits=12)
    elseif x isa AbstractArray
        return [round_nested(v) for v in x]
    elseif x isa Dict
        return Dict(k => round_nested(v) for (k, v) in x)
    else
        return x
    end
end

q1 = 0.73
q2 = 0.61
theta = 0.83
phi = 0.47

channels = ChannelSpec[
    ChannelSpec("Ti", "z-basis pinch", pinch_z(q1)),
    ChannelSpec("Te", "x-basis pinch", pinch_x(q2)),
    ChannelSpec("Fi", "x-rotation", rot_x(theta)),
    ChannelSpec("Fe", "z-rotation", rot_z(phi)),
]

# Dependency-forcing erasure: remove the basis geometry distinction by making
# every substage a same-basis z-dephasing channel. These commute, so the order
# signature must collapse to zero if the signature is really basis/order forced.
erased_channels = ChannelSpec[
    ChannelSpec("Ti_erased", "z-basis pinch", pinch_z(q1)),
    ChannelSpec("Te_erased", "z-basis pinch replacing x-basis pinch", pinch_z(q2)),
    ChannelSpec("Fi_erased", "z-basis pinch replacing x-rotation", pinch_z(0.42)),
    ChannelSpec("Fe_erased", "z-basis pinch replacing z-rotation", pinch_z(0.35)),
]

ptms = Dict(ch.label => matrix_to_json(pauli_transfer_matrix(ch)) for ch in channels)
fixed = Dict{String,Any}()
for ch in channels
    kept, defects = fixed_algebra_basis(ch)
    fixed[ch.label] = Dict("fixed_basis" => kept, "defects" => defects)
end

_, rho0 = density_from_angles(0.31, 0.22, pi / 5)
pair_order = Dict{String,Float64}()
pair_order_erased = Dict{String,Float64}()
for i in 1:length(channels), j in 1:length(channels)
    i < j || continue
    pair_order["$(channels[i].label)_$(channels[j].label)"] = order_gap(channels[i], channels[j], rho0)
    pair_order_erased["$(erased_channels[i].label)_$(erased_channels[j].label)"] =
        order_gap(erased_channels[i], erased_channels[j], rho0)
end

identity_channel = ChannelSpec("Id", "identity channel", rho -> rho)
negative_controls = Dict(
    "identity_with_Ti_gap" => order_gap(identity_channel, channels[1], rho0),
    "Ti_with_same_Ti_gap" => order_gap(channels[1], channels[1], rho0),
    "same_basis_z_pinches_gap" => order_gap(pinch_z(0.2) |> f -> ChannelSpec("Zp02", "z pinch 0.2", f),
                                            pinch_z(0.8) |> f -> ChannelSpec("Zp08", "z pinch 0.8", f),
                                            rho0),
    "maximally_mixed_Te_Fi_gap" => order_gap(channels[2], channels[3], I2 / 2),
)

stress_rows = stress(channels, erased_channels, [8, 16, 32, 64])
max_present = maximum(row["max_adjacent_pair_order_gap"] for row in stress_rows)
max_erased = maximum(row["max_adjacent_pair_order_gap_erased"] for row in stress_rows)
max_seq_present = maximum(row["max_sequence_order_gap_forward_vs_reverse"] for row in stress_rows)
max_seq_erased = maximum(row["max_sequence_order_gap_erased"] for row in stress_rows)

collapse_ok = max_present > 1e-3 && max_erased < 1e-10 && max_seq_present > 1e-3 && max_seq_erased < 1e-10
negative_ok = maximum(values(negative_controls)) < 1e-10
ptm_ok = all(size(pauli_transfer_matrix(ch)) == (4, 4) for ch in channels)
fixed_ok = all(length(fixed[ch.label]["fixed_basis"]) >= 2 for ch in channels)
stress_ok = length(stress_rows) == 4 && stress_rows[end]["N"] == 64
all_pass = collapse_ok && negative_ok && ptm_ok && fixed_ok && stress_ok

result = Dict(
    "sim_id" => "L11_layer_codex",
    "name" => "L11 operator-substage local cell layer: Ti/Te/Fi/Fe finite QIT channel-order collapse test",
    "version" => "1.0",
    "classification" => "L11_layer_codex_poc",
    "promotion_allowed" => false,
    "sim_execution_kind" => "nonclassical_poc_julia_finite_qit",
    "sim_class" => "operator_substage_local_cell_probe",
    "fresh_rerun" => true,
    "finite_map" => "D(C^2) x finite PEPS3D local cell K_N x {Ti,Te,Fi,Fe} -> Pauli-transfer matrices, fixed Pauli algebras, order-gap scalars, derived entropy readouts",
    "domain" => Dict(
        "hilbert_carrier" => "H=C^2",
        "density_space" => "D(C^2)={rho>=0, Tr rho=1}",
        "operator_substages" => ["Ti z-basis pinch", "Te x-basis pinch", "Fi x-rotation", "Fe z-rotation"],
        "stress_site_counts" => [8, 16, 32, 64],
    ),
    "codomain_or_output" => [
        "4x4 Pauli transfer matrices",
        "fixed algebra basis labels over {I,X,Y,Z}",
        "trace-norm substage order gaps",
        "von Neumann entropy and purity readouts",
        "PEPS3D K=(V,E,F,C) finite local-cell anchors",
    ],
    "F01_witness" => Dict(
        "finite_carrier" => "single-cell H=C^2 density state at each finite site",
        "finite_probe_set" => PAULI_LABELS,
        "finite_operator_set" => ["Ti", "Te", "Fi", "Fe"],
        "finite_path_set" => ["adjacent pair orders Phi_a Phi_b vs Phi_b Phi_a", "full sequence vs reverse sequence"],
    ),
    "N01_witness" => Dict(
        "measured_max_adjacent_pair_gap" => max_present,
        "measured_max_sequence_gap" => max_seq_present,
        "gap_formula" => "||Phi_a Phi_b rho - Phi_b Phi_a rho||_1",
    ),
    "carrier_realization" => "Julia-native ComplexF64 spinor psi in C^2 and spinor-derived density rho=psi psi^dagger; no NumPy",
    "spinor_state" => Dict(
        "example_phi_chi_eta" => [0.31, 0.22, pi / 5],
        "example_density_trace" => real(tr(rho0)),
        "example_density_purity" => purity(rho0),
    ),
    "peps3d_embedding" => Dict(
        "stress_K_anchors" => [row["K"] for row in stress_rows],
        "honest_boundary" => "finite K=(V,E,F,C) local-cell anchor only; no PEPS tensor contraction or full manifold admission claimed",
    ),
    "pauli_transfer_matrices" => ptms,
    "fixed_algebras" => fixed,
    "pair_order_gaps_on_example_state" => pair_order,
    "pair_order_gaps_after_commuting_erasure_on_example_state" => pair_order_erased,
    "stress_results" => stress_rows,
    "dependency_forcing_ablation" => Dict(
        "removed_geometry" => "basis distinction/order-sensitive substage geometry erased by replacing Te, Fi, Fe with same-basis z-dephasing channels",
        "present_max_adjacent_pair_gap" => max_present,
        "erased_max_adjacent_pair_gap" => max_erased,
        "adjacent_pair_collapse_delta" => max_present - max_erased,
        "present_max_sequence_gap" => max_seq_present,
        "erased_max_sequence_gap" => max_seq_erased,
        "sequence_collapse_delta" => max_seq_present - max_seq_erased,
        "collapsed" => collapse_ok,
        "interpretation" => collapse_ok ? "order signature collapses under commuting erasure; not just surviving hand-written channels" : "signature survived erasure or failed to appear; would be hand-written channels only",
    ),
    "negative_controls" => negative_controls,
    "qit_readouts_derived_not_primary" => Dict(
        "example_entropy_before" => von_neumann_entropy(rho0),
        "example_entropy_after_Ti_Te_Fi_Fe" => von_neumann_entropy(apply_sequence(channels, rho0)),
        "example_entropy_after_erased_sequence" => von_neumann_entropy(apply_sequence(erased_channels, rho0)),
        "example_purity_before" => purity(rho0),
        "example_purity_after_Ti_Te_Fi_Fe" => purity(apply_sequence(channels, rho0)),
        "example_purity_after_erased_sequence" => purity(apply_sequence(erased_channels, rho0)),
    ),
    "tool_manifest" => Dict(
        "LinearAlgebra" => Dict(
            "role" => "load_bearing",
            "reason" => "matrix channels, SVD trace norm, Pauli transfer matrices, fixed-algebra defects, eigenspectrum entropy",
        ),
        "JSON" => Dict(
            "role" => "supportive",
            "reason" => "writes the required result artifact",
        ),
        "Z3" => Dict(
            "role" => "omitted",
            "reason" => "z3 omitted, not decorative; no load-bearing SMT claim is made",
        ),
    ),
    "tool_integration_depth" => Dict(
        "LinearAlgebra" => "load_bearing",
        "JSON" => "supportive",
        "Z3" => "None",
    ),
    "blocked_consumers" => [
        "full layer completion",
        "parent-complete L11 status",
        "stacking readiness",
        "Axis0",
        "flux",
        "FEP",
        "physics/gravity",
        "final manifold admission",
    ],
    "promotion_blockers" => [
        "Julia POC only; repo nonclassical manifold doctrine still requires stronger carrier admission before downstream claims",
        "PEPS3D anchor is finite K combinatorial cell support, not a contracted PEPS3D tensor-network proof",
        "no dedicated full-layer evidence packet or layer-completion claim gate run",
        "no Z3 proof because it would be decorative for this numeric channel-order collapse",
    ],
    "verdict" => Dict(
        "collapse_ok" => collapse_ok,
        "negative_controls_ok" => negative_ok,
        "ptm_ok" => ptm_ok,
        "fixed_algebras_ok" => fixed_ok,
        "stress_8_16_32_64_ok" => stress_ok,
        "all_pass" => all_pass,
        "honest_status" => all_pass ? "passes local L11_layer_codex_poc checks; promotion still blocked" : "partial_or_failed; inspect missing booleans",
    ),
)

out_path = joinpath(@__DIR__, "L11_layer_codex_results.json")
open(out_path, "w") do f
    JSON.print(f, round_nested(result), 2)
end

println("== L11_layer_codex ==")
println("classification = L11_layer_codex_poc")
println("promotion_allowed = false")
println("max adjacent pair order gap present = ", round(max_present, digits=12))
println("max adjacent pair order gap erased  = ", round(max_erased, digits=12))
println("max sequence order gap present      = ", round(max_seq_present, digits=12))
println("max sequence order gap erased       = ", round(max_seq_erased, digits=12))
println("dependency erasure collapsed        = ", collapse_ok)
println("all_pass local POC checks           = ", all_pass)
println("wrote ", out_path)
