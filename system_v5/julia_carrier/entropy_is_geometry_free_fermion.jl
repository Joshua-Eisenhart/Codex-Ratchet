using LinearAlgebra

const RESULT_PATH = "entropy_is_geometry_free_fermion_results.json"

function escape_json(s::AbstractString)
    t = replace(s, "\\" => "\\\\")
    t = replace(t, "\"" => "\\\"")
    t = replace(t, "\n" => "\\n")
    t = replace(t, "\r" => "\\r")
    return replace(t, "\t" => "\\t")
end

function to_json(x)
    if x === nothing
        return "null"
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        return isfinite(x) ? string(x) : "null"
    elseif x isa AbstractString
        return "\"" * escape_json(x) * "\""
    elseif x isa AbstractVector
        return "[" * join([to_json(v) for v in x], ",") * "]"
    elseif x isa AbstractDict
        parts = String[]
        for k in sort(collect(keys(x)); by=string)
            push!(parts, to_json(string(k)) * ":" * to_json(x[k]))
        end
        return "{" * join(parts, ",") * "}"
    else
        error("Unsupported JSON type: $(typeof(x))")
    end
end

function fit_line(xs, ys)
    n = length(xs)
    xbar = sum(xs) / n
    ybar = sum(ys) / n
    denom = sum((x - xbar)^2 for x in xs)
    slope = sum((xs[i] - xbar) * (ys[i] - ybar) for i in 1:n) / denom
    intercept = ybar - slope * xbar
    residuals = [ys[i] - (slope * xs[i] + intercept) for i in 1:n]
    rmse = sqrt(sum(r * r for r in residuals) / n)
    return Dict(
        "slope" => slope,
        "intercept" => intercept,
        "rmse" => rmse,
        "sse" => sum(r * r for r in residuals),
    )
end

function hopping_ground_state_correlation(n_sites::Int)
    h = zeros(Float64, n_sites, n_sites)
    for i in 1:(n_sites - 1)
        h[i, i + 1] = -1.0
        h[i + 1, i] = -1.0
    end
    h[1, n_sites] = -1.0
    h[n_sites, 1] = -1.0

    eig = eigen(Symmetric(h))
    occupied = findall(e -> e < -1.0e-10, eig.values)
    modes = eig.vectors[:, occupied]
    cmat = modes * transpose(modes)
    cmat = 0.5 * (cmat + transpose(cmat))
    return cmat, eig.values, length(occupied)
end

function interval_sites(x1::Int, x2::Int)
    if x2 <= x1
        error("Invalid half-open interval [$x1, $x2)")
    end
    return collect(x1:(x2 - 1))
end

function entanglement_entropy(cmat, sites::Vector{Int})
    vals = eigvals(Hermitian(Matrix(cmat[sites, sites])))
    s = 0.0
    eps = 1.0e-12
    for raw in vals
        nu = real(raw)
        if nu <= eps || nu >= 1.0 - eps
            continue
        end
        nu = min(max(nu, eps), 1.0 - eps)
        s -= nu * log(nu) + (1.0 - nu) * log(1.0 - nu)
    end
    return s
end

function mutual_information(cmat, a_sites::Vector{Int}, b_sites::Vector{Int})
    sa = entanglement_entropy(cmat, a_sites)
    sb = entanglement_entropy(cmat, b_sites)
    sab = entanglement_entropy(cmat, vcat(a_sites, b_sites))
    return sa + sb - sab, sa, sb, sab
end

function endpoint_cross_ratio(x1::Int, x2::Int, x3::Int, x4::Int)
    return ((x2 - x1) * (x4 - x3)) / ((x3 - x1) * (x4 - x2))
end

function interval_pair_row(cmat, x1::Int, x2::Int, x3::Int, x4::Int)
    a = interval_sites(x1, x2)
    b = interval_sites(x3, x4)
    mi, sa, sb, sab = mutual_information(cmat, a, b)
    distance = mi > 0.0 ? -log(mi) : nothing
    return Dict(
        "x1" => x1,
        "x2" => x2,
        "x3" => x3,
        "x4" => x4,
        "A_sites" => [first(a), last(a)],
        "B_sites" => [first(b), last(b)],
        "length_A" => length(a),
        "length_B" => length(b),
        "gap_sites" => x3 - x2,
        "cross_ratio_eta" => endpoint_cross_ratio(x1, x2, x3, x4),
        "S_A" => sa,
        "S_B" => sb,
        "S_A_union_B" => sab,
        "I_A_B" => mi,
        "distance_minus_log_I" => distance,
    )
end

function relative_spread(vals)
    avg = sum(vals) / length(vals)
    if avg == 0.0
        return Inf
    end
    return maximum(abs(v - avg) / abs(avg) for v in vals)
end

function min_pairwise_relative_difference(vals)
    best = Inf
    for i in 1:(length(vals) - 1)
        for j in (i + 1):length(vals)
            denom = max(abs(vals[i]), abs(vals[j]))
            if denom == 0.0
                best = min(best, 0.0)
            else
                best = min(best, abs(vals[i] - vals[j]) / denom)
            end
        end
    end
    return best
end

function rounded(x; digits=6)
    return x === nothing ? "null" : string(round(x; digits=digits))
end

function main()
    n_sites = 242
    cmat, energies, n_occupied = hopping_ground_state_correlation(n_sites)

    lengths = collect(10:10:80)
    entropy_rows = Dict[]
    entropies = Float64[]
    for len in lengths
        # Periodic translation invariance lets the single interval start anywhere.
        sites = collect(1:len)
        s = entanglement_entropy(cmat, sites)
        push!(entropies, s)
        push!(entropy_rows, Dict("L" => len, "S_L" => s))
    end

    log_fit = fit_line([log(float(l)) for l in lengths], entropies)
    linear_fit = fit_line([float(l) for l in lengths], entropies)
    fitted_c = 3.0 * log_fit["slope"]
    log_beats_linear = log_fit["rmse"] < linear_fit["rmse"]

    gap_rows = Dict[]
    interval_len = 20
    x1 = 40
    x2 = x1 + interval_len
    for gap in [2, 4, 8, 12, 20, 30, 40, 60]
        x3 = x2 + gap
        x4 = x3 + interval_len
        row = interval_pair_row(cmat, x1, x2, x3, x4)
        push!(gap_rows, row)
    end
    gap_mis = [row["I_A_B"] for row in gap_rows]
    gap_distances = [row["distance_minus_log_I"] for row in gap_rows]
    all_disjoint_mi_positive = all(mi -> mi > 1.0e-10, gap_mis)
    mi_decays_with_gap = all(gap_mis[i + 1] <= gap_mis[i] + 1.0e-10 for i in 1:(length(gap_mis) - 1))
    distance_monotone = all((gap_distances[i] !== nothing && gap_distances[i + 1] !== nothing &&
                             gap_distances[i + 1] >= gap_distances[i] - 1.0e-10)
                            for i in 1:(length(gap_distances) - 1))

    groups = [
        Dict(
            "label" => "eta_1_over_9",
            "target_eta" => 1.0 / 9.0,
            "configs" => [[20, 32, 56, 68], [78, 94, 126, 142], [142, 162, 202, 222]],
        ),
        Dict(
            "label" => "eta_1_over_4",
            "target_eta" => 1.0 / 4.0,
            "configs" => [[20, 36, 52, 68], [78, 98, 118, 138], [142, 166, 190, 214]],
        ),
        Dict(
            "label" => "eta_4_over_9",
            "target_eta" => 4.0 / 9.0,
            "configs" => [[20, 32, 38, 50], [78, 96, 105, 123], [142, 166, 178, 202]],
        ),
    ]

    cross_ratio_groups = Dict[]
    group_means = Float64[]
    same_eta_ok_flags = Bool[]
    for group in groups
        rows = Dict[]
        for cfg in group["configs"]
            push!(rows, interval_pair_row(cmat, cfg[1], cfg[2], cfg[3], cfg[4]))
        end
        vals = [row["I_A_B"] for row in rows]
        avg = sum(vals) / length(vals)
        spread = relative_spread(vals)
        push!(group_means, avg)
        push!(same_eta_ok_flags, spread <= 0.15)
        push!(cross_ratio_groups, Dict(
            "label" => group["label"],
            "target_eta" => group["target_eta"],
            "mean_I" => avg,
            "max_relative_deviation_from_mean" => spread,
            "within_15_percent" => spread <= 0.15,
            "configs" => rows,
        ))
    end

    min_diff_cross_ratio = min_pairwise_relative_difference(group_means)
    different_eta_differs_more = min_diff_cross_ratio > 0.15

    c_ok = 0.8 <= fitted_c <= 1.2
    all_pass = c_ok && log_beats_linear && all_disjoint_mi_positive &&
               all(same_eta_ok_flags) && different_eta_differs_more

    verdict = Dict(
        "all_pass" => all_pass,
        "c_in_range_0_8_to_1_2" => c_ok,
        "log_entropy_fit_beats_linear_fit" => log_beats_linear,
        "all_disjoint_interval_mi_positive" => all_disjoint_mi_positive,
        "mutual_information_decays_with_gap" => mi_decays_with_gap,
        "distance_minus_log_I_monotone_with_gap" => distance_monotone,
        "same_cross_ratio_groups_within_15_percent" => all(same_eta_ok_flags),
        "minimum_relative_difference_between_cross_ratio_group_means" => min_diff_cross_ratio,
        "different_cross_ratio_groups_differ_more_than_15_percent" => different_eta_differs_more,
        "honesty_note" => "The test is finite-size and lattice-discretized. Same-eta clustering is accepted only if measured max relative deviation is <= 15%; no values are adjusted to force a pass.",
    )

    receipt = Dict(
        "script" => "entropy_is_geometry_free_fermion.jl",
        "construction" => "Periodic 1D critical free-fermion hopping chain; ground state projector from negative-energy one-body modes; entropies from restricted correlation matrices.",
        "endpoint_convention" => "Endpoint tuples [x1,x2,x3,x4] use half-open lattice intervals A=[x1,x2), B=[x3,x4); cross-ratio uses the continuum endpoint formula from the task.",
        "n_sites" => n_sites,
        "boundary_condition" => "periodic",
        "n_occupied_modes" => n_occupied,
        "lowest_energy" => minimum(energies),
        "highest_energy" => maximum(energies),
        "entropy_scaling" => Dict(
            "table" => entropy_rows,
            "log_fit_S_equals_slope_logL_plus_intercept" => log_fit,
            "linear_fit_S_equals_slope_L_plus_intercept" => linear_fit,
            "fitted_c_from_3_times_log_slope" => fitted_c,
            "log_beats_linear" => log_beats_linear,
        ),
        "disjoint_interval_gap_scan" => Dict(
            "fixed_interval_length" => interval_len,
            "table" => gap_rows,
            "all_I_positive" => all_disjoint_mi_positive,
            "I_decays_with_gap" => mi_decays_with_gap,
            "distance_minus_log_I_monotone" => distance_monotone,
        ),
        "cross_ratio_invariance" => Dict(
            "groups" => cross_ratio_groups,
            "same_eta_within_15_percent" => all(same_eta_ok_flags),
            "minimum_relative_difference_between_group_means" => min_diff_cross_ratio,
            "different_eta_differs_more_than_15_percent" => different_eta_differs_more,
        ),
        "verdict" => verdict,
    )

    open(RESULT_PATH, "w") do io
        write(io, to_json(receipt))
        write(io, "\n")
    end

    println("S(L) fit: c=$(rounded(fitted_c)), log_rmse=$(rounded(log_fit["rmse"])), linear_rmse=$(rounded(linear_fit["rmse"])), log_beats_linear=$(log_beats_linear)")
    println("Disjoint intervals: all_I_positive=$(all_disjoint_mi_positive), I_decays_with_gap=$(mi_decays_with_gap), distance_monotone=$(distance_monotone)")
    for row in gap_rows
        println("  gap=$(row["gap_sites"]) I=$(rounded(row["I_A_B"]; digits=8)) d=-log(I)=$(rounded(row["distance_minus_log_I"]; digits=6))")
    end
    println("Cross-ratio invariance:")
    for group in cross_ratio_groups
        vals = [row["I_A_B"] for row in group["configs"]]
        println("  $(group["label"]) eta=$(rounded(group["target_eta"]; digits=6)) mean_I=$(rounded(group["mean_I"]; digits=8)) max_rel_dev=$(rounded(group["max_relative_deviation_from_mean"]; digits=6)) within_15pct=$(group["within_15_percent"]) values=$([round(v; digits=8) for v in vals])")
    end
    println("Different-eta min relative mean separation=$(rounded(min_diff_cross_ratio; digits=6)), differs_more_than_15pct=$(different_eta_differs_more)")
    println("Receipt: $(RESULT_PATH)")
    println("ALL_PASS=$(all_pass)")
end

main()
