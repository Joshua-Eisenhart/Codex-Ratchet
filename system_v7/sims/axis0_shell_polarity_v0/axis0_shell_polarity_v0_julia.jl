using JSON
using LinearAlgebra
using Statistics

ROOT = @__DIR__
OUT = joinpath(ROOT, "axis0_shell_polarity_v0_julia_results.json")

entropy_probs(p) = -sum(x * log(x) for x in p if x > 1e-12)

function entropy_density(rho)
    vals = eigvals(Hermitian((rho + rho') / 2))
    vals = [max(real(v), 0.0) for v in vals if real(v) > 1e-12]
    return -sum(v * log(v) for v in vals)
end

function partial_trace_i(rho)
    out = zeros(Float64, 2, 2)
    for b in 1:2, i in 1:2, j in 1:2
        out[i, j] += rho[(i - 1) * 2 + b, (j - 1) * 2 + b]
    end
    return out
end

function partial_trace_b(rho)
    out = zeros(Float64, 2, 2)
    for i in 1:2, b in 1:2, c in 1:2
        out[b, c] += rho[(i - 1) * 2 + b, (i - 1) * 2 + c]
    end
    return out
end

function bell_mixture(q)
    psi = [1.0, 0.0, 0.0, 1.0] / sqrt(2.0)
    bell = psi * psi'
    prod = Matrix(I, 4, 4) / 4.0
    return q * bell + (1.0 - q) * Matrix(prod)
end

function kraus_family(commuting=false)
    if commuting
        return [Diagonal([0.94, 0.70]) |> Matrix, Diagonal([0.34, 0.71]) |> Matrix]
    end
    return [[0.92 0.00; 0.00 0.55], [0.00 0.62; 0.30 0.00]]
end

function path_weight(seq, Ks, rho_b)
    K = Matrix(I, 2, 2)
    for idx in seq
        K = Ks[idx] * K
    end
    raw = K * rho_b * K'
    return max(real(tr(raw)), 1e-12)
end

function shell_components(r, regime, control)
    open_regime = regime == "open"
    area = control == "no_shell_radius" ? 1.0 : Float64(r * r)
    radius_bias = control == "no_shell_radius" ? 0.0 : log1p(r)
    q = open_regime ? 0.18 + 0.04 * r : 0.70 - 0.035 * r
    q = control == "product_no_entanglement_cut" ? 0.0 : clamp(q, 0.02, 0.92)
    rho = bell_mixture(q)
    rho_b = partial_trace_b(rho)
    rho_i = partial_trace_i(rho)
    s_b = entropy_density(rho_b)
    s_ib = entropy_density(rho)
    s_i = entropy_density(rho_i)
    ic = s_b - s_ib
    mi = s_i + s_b - s_ib
    k_binding = mi + max(ic, 0.0)
    Ks = kraus_family(control == "commuting_path_family")
    paths = [(1, 2), (2, 1), (1, 1), (2, 2)]
    weights = [path_weight(p, Ks, rho_b) for p in paths]
    if control == "one_future_control"
        keep = argmax(weights)
        weights = [i == keep ? weights[keep] : 0.0 for i in 1:4]
    end
    if control == "scrambled_Omega"
        weights = weights[[3, 1, 4, 2]]
    end
    probs = weights / sum(weights)
    gap = norm(Ks[2] * Ks[1] - Ks[1] * Ks[2])
    return Dict(
        "H_Omega" => entropy_probs(probs) + (open_regime ? 0.22 : -0.06) * radius_bias,
        "S_B" => s_b + (open_regime ? 0.035 * area / 36.0 : -0.018 * r),
        "K_binding" => k_binding,
        "log_Z_path" => log(sum(weights)),
        "order_gap" => gap,
        "I_c" => ic,
    )
end

function deltas(rows, key)
    vals = [row[key] for row in rows]
    return vcat([0.0], [vals[i] - vals[i - 1] for i in 2:length(vals)])
end

function regime_table(regime, control="baseline")
    raw = [shell_components(r, regime, control) for r in 1:6]
    dh = deltas(raw, "H_Omega")
    ds = deltas(raw, "S_B")
    return [Dict(
        "r" => i,
        "Delta_H_Omega" => dh[i],
        "Delta_S_B" => ds[i],
        "K_binding" => raw[i]["K_binding"],
        "log_Z_path" => raw[i]["log_Z_path"],
        "order_gap" => raw[i]["order_gap"],
        "I_c" => raw[i]["I_c"],
    ) for i in 1:6]
end

function means(table)
    keys = ["Delta_H_Omega", "Delta_S_B", "K_binding", "log_Z_path", "order_gap", "I_c"]
    return Dict(k => mean([row[k] for row in table]) for k in keys)
end

open_table = regime_table("open")
binding_table = regime_table("binding")
result = Dict(
    "sim_id" => "axis0_shell_polarity_v0",
    "engine" => "julia",
    "classification" => "scratch_diagnostic",
    "promotion_allowed" => false,
    "capstone" => "DRAFT_UNAUDITED",
    "axis0_near_object" => "shell-polarity readout",
    "component_means" => Dict("open" => means(open_table), "binding" => means(binding_table)),
    "component_table" => Dict("open" => open_table, "binding" => binding_table),
)
open(OUT, "w") do io
    JSON.print(io, result, 2)
    println(io)
end
println(JSON.json(Dict("wrote" => OUT)))
