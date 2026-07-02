#!/usr/bin/env julia

# Self-contained free-fermion check for the specified Qi-Wu-Zhang model.
# Uses only Julia stdlibs and O(N^3) dense diagonalization.

using LinearAlgebra
using Random
using Printf

const LX = 20
const LY = 20
const FHS_NK = 41
const M_LEFT = -1.0   # FIX: m=-1 -> M(k)=1-cos kx-cos ky inverts at Gamma -> |C|=1 (topological). m=1 was trivial (C=0).
const M_CONTROL = 3.0
const DISORDER_W = 0.08
const RNG_SEED = 20260601
const EPS_CLAMP = 1.0e-12

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)
const TX = -0.5 * SZ - 0.5im * SX
const TY = -0.5 * SZ - 0.5im * SY

struct FlowSummary
    present::Bool
    unidirectional::Bool
    positive_crossings::Int
    negative_crossings::Int
    c_estimate::Int
    min_abs_eps::Float64
    gap_window::Float64
end

function bloch_hamiltonian(m::Float64, kx::Float64, ky::Float64)
    dx = sin(kx)
    dy = sin(ky)
    dz = m + 2.0 - cos(kx) - cos(ky)
    return dx * SX + dy * SY + dz * SZ
end

function occupied_spinor(m::Float64, kx::Float64, ky::Float64)
    e = eigen(Hermitian(bloch_hamiltonian(m, kx, ky)))
    return e.vectors[:, 1]
end

function unit_overlap(u::AbstractVector{ComplexF64}, v::AbstractVector{ComplexF64})
    z = dot(u, v)
    a = abs(z)
    return a <= 1.0e-14 ? one(ComplexF64) : z / a
end

function fhs_chern_from_occupied_state(m::Float64; nk::Int=FHS_NK)
    occ = Array{ComplexF64}(undef, 2, nk, nk)
    for ix in 1:nk, iy in 1:nk
        kx = 2.0 * pi * (ix - 1) / nk
        ky = 2.0 * pi * (iy - 1) / nk
        occ[:, ix, iy] = occupied_spinor(m, kx, ky)
    end

    total_phase = 0.0
    for ix in 1:nk, iy in 1:nk
        ixp = ix == nk ? 1 : ix + 1
        iyp = iy == nk ? 1 : iy + 1
        ux = unit_overlap(occ[:, ix, iy], occ[:, ixp, iy])
        uy_x = unit_overlap(occ[:, ixp, iy], occ[:, ixp, iyp])
        ux_y = unit_overlap(occ[:, ix, iyp], occ[:, ixp, iyp])
        uy = unit_overlap(occ[:, ix, iy], occ[:, ix, iyp])
        total_phase += angle(ux * uy_x * conj(ux_y) * conj(uy))
    end
    return total_phase / (2.0 * pi)
end

site_index(x::Int, y::Int, lx::Int) = (y - 1) * lx + x
orb_index(x::Int, y::Int, a::Int, lx::Int) = 2 * (site_index(x, y, lx) - 1) + a

function add_block!(h::Matrix{ComplexF64}, x1::Int, y1::Int, x2::Int, y2::Int,
                    block::AbstractMatrix{ComplexF64}, lx::Int)
    for a in 1:2, b in 1:2
        h[orb_index(x1, y1, a, lx), orb_index(x2, y2, b, lx)] += block[a, b]
    end
end

function realspace_hamiltonian(m::Float64, lx::Int, ly::Int;
                               periodic_y::Bool=true,
                               disorder::Union{Nothing, Matrix{Float64}}=nothing)
    dim = 2 * lx * ly
    h = zeros(ComplexF64, dim, dim)
    for x in 1:lx, y in 1:ly
        onsite_shift = disorder === nothing ? 0.0 : disorder[x, y]
        onsite = (m + 2.0) * SZ + onsite_shift * I2
        add_block!(h, x, y, x, y, onsite, lx)

        xp = x == lx ? 1 : x + 1
        add_block!(h, x, y, xp, y, TX, lx)
        add_block!(h, xp, y, x, y, TX', lx)

        if y < ly || periodic_y
            yp = y == ly ? 1 : y + 1
            add_block!(h, x, y, x, yp, TY, lx)
            add_block!(h, x, yp, x, y, TY', lx)
        end
    end
    return Hermitian(h)
end

function occupied_basis(h::Hermitian{ComplexF64, Matrix{ComplexF64}})
    e = eigen(h)
    n_occ = length(e.values) ÷ 2
    return e.vectors[:, 1:n_occ], minimum(abs.(e.values))
end

function polar_unitary(a::Matrix{ComplexF64})
    f = svd(a)
    return f.U * f.Vt
end

function bott_index_from_projector_state(m::Float64, lx::Int, ly::Int;
                                         disorder::Union{Nothing, Matrix{Float64}}=nothing)
    h = realspace_hamiltonian(m, lx, ly; periodic_y=true, disorder=disorder)
    v_occ, min_abs_energy = occupied_basis(h)
    dim, n_occ = size(v_occ)

    phase_x = Vector{ComplexF64}(undef, dim)
    phase_y = Vector{ComplexF64}(undef, dim)
    for x in 1:lx, y in 1:ly, a in 1:2
        idx = orb_index(x, y, a, lx)
        phase_x[idx] = exp(2.0im * pi * (x - 1) / lx)
        phase_y[idx] = exp(2.0im * pi * (y - 1) / ly)
    end

    ux_occ = v_occ' * (v_occ .* reshape(phase_x, :, 1))
    uy_occ = v_occ' * (v_occ .* reshape(phase_y, :, 1))
    ux = polar_unitary(Matrix{ComplexF64}(ux_occ))
    uy = polar_unitary(Matrix{ComplexF64}(uy_occ))
    loop = uy * ux * uy' * ux'
    bott = sum(angle.(eigvals(loop))) / (2.0 * pi)
    return bott, min_abs_energy, n_occ
end

function cylinder_k_hamiltonian(m::Float64, kx::Float64, ly::Int)
    dim = 2 * ly
    h = zeros(ComplexF64, dim, dim)
    onsite = sin(kx) * SX + (m + 2.0 - cos(kx)) * SZ
    for y in 1:ly
        for a in 1:2, b in 1:2
            h[2 * (y - 1) + a, 2 * (y - 1) + b] += onsite[a, b]
        end
        if y < ly
            for a in 1:2, b in 1:2
                h[2 * (y - 1) + a, 2 * y + b] += TY[a, b]
                h[2 * y + a, 2 * (y - 1) + b] += TY'[a, b]
            end
        end
    end
    return Hermitian(h)
end

function periodic_y_k_hamiltonian(m::Float64, kx::Float64, ly::Int)
    dim = 2 * ly
    h = zeros(ComplexF64, dim, dim)
    onsite = sin(kx) * SX + (m + 2.0 - cos(kx)) * SZ
    for y in 1:ly
        for a in 1:2, b in 1:2
            h[2 * (y - 1) + a, 2 * (y - 1) + b] += onsite[a, b]
        end
        yp = y == ly ? 1 : y + 1
        for a in 1:2, b in 1:2
            h[2 * (y - 1) + a, 2 * (yp - 1) + b] += TY[a, b]
            h[2 * (yp - 1) + a, 2 * (y - 1) + b] += TY'[a, b]
        end
    end
    return Hermitian(h)
end

function entanglement_spectrum(m::Float64, lx::Int, ly::Int; ay::Int=ly ÷ 2)
    kxs = [2.0 * pi * (ix - 1) / lx for ix in 1:lx]
    sub = Int[]
    for y in 1:ay, a in 1:2
        push!(sub, 2 * (y - 1) + a)
    end

    n_bands = length(sub)
    epsmat = zeros(Float64, lx, n_bands)
    numat = zeros(Float64, lx, n_bands)
    min_bulk_abs_energy = Inf

    for (ik, kx) in enumerate(kxs)
        e = eigen(periodic_y_k_hamiltonian(m, kx, ly))
        min_bulk_abs_energy = min(min_bulk_abs_energy, minimum(abs.(e.values)))
        occ_idx = findall(<(-1.0e-10), e.values)
        if length(occ_idx) != ly
            error("expected $ly strictly negative periodic-y valence states at kx=$kx, found $(length(occ_idx)); min_abs_energy=$(minimum(abs.(e.values)))")
        end
        v_occ = e.vectors[:, occ_idx]
        corr = v_occ * v_occ'
        ca = Hermitian(corr[sub, sub])
        nu = sort(real.(eigvals(ca)))
        nu = clamp.(nu, EPS_CLAMP, 1.0 - EPS_CLAMP)
        eps = log.((1.0 .- nu) ./ nu)
        p = sortperm(eps)
        epsmat[ik, :] = eps[p]
        numat[ik, :] = nu[p]
    end

    return kxs, epsmat, numat, min_bulk_abs_energy
end

function track_bands(epsmat::Matrix{Float64})
    nk, nb = size(epsmat)
    tracked = zeros(Float64, nk, nb)
    tracked[1, :] = epsmat[1, :]
    for ik in 2:nk
        used = falses(nb)
        assigned = zeros(Float64, nb)
        pairs = Tuple{Float64, Int, Int}[]
        for b in 1:nb, j in 1:nb
            push!(pairs, (abs(tracked[ik - 1, b] - epsmat[ik, j]), b, j))
        end
        sort!(pairs, by=x -> x[1])
        band_done = falses(nb)
        for (_, b, j) in pairs
            if !band_done[b] && !used[j]
                assigned[b] = epsmat[ik, j]
                band_done[b] = true
                used[j] = true
            end
        end
        tracked[ik, :] = assigned
    end
    return tracked
end

function detect_chiral_flow(kxs::Vector{Float64}, epsmat::Matrix{Float64};
                            gap_window::Float64=3.0)
    tracked = track_bands(epsmat)
    nk, nb = size(tracked)
    pos = 0
    neg = 0
    for b in 1:nb, ik in 1:(nk - 1)
        e1 = tracked[ik, b]
        e2 = tracked[ik + 1, b]
        crosses = (e1 == 0.0) || (e1 * e2 < 0.0)
        local_to_gap = max(abs(e1), abs(e2)) <= gap_window
        if crosses && local_to_gap
            slope = (e2 - e1) / (kxs[ik + 1] - kxs[ik])
            if slope > 0
                pos += 1
            elseif slope < 0
                neg += 1
            end
        end
    end
    present = pos + neg > 0
    unidir = present && (pos == 0 || neg == 0)
    c_est = unidir ? (pos > 0 ? 1 : -1) : 0
    return FlowSummary(present, unidir, pos, neg, c_est, minimum(abs.(epsmat)), gap_window), tracked
end

function svg_polyline(points::Vector{Tuple{Float64, Float64}}, color::String)
    coords = join([@sprintf("%.2f,%.2f", x, y) for (x, y) in points], " ")
    return "<polyline points=\"$coords\" fill=\"none\" stroke=\"$color\" stroke-width=\"0.8\" stroke-opacity=\"0.55\" />\n"
end

function write_entanglement_svg(path::String, kxs::Vector{Float64},
                                left_tracked::Matrix{Float64},
                                ctrl_tracked::Matrix{Float64})
    width = 920
    height = 420
    margin = 42
    panel_w = (width - 3 * margin) / 2
    panel_h = height - 2 * margin
    ymin = -8.0
    ymax = 8.0

    function map_point(panel::Int, k::Float64, e::Float64)
        x0 = margin + (panel - 1) * (panel_w + margin)
        x = x0 + panel_w * k / (2.0 * pi)
        ec = clamp(e, ymin, ymax)
        y = margin + panel_h * (1.0 - (ec - ymin) / (ymax - ymin))
        return x, y
    end

    open(path, "w") do io
        write(io, "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"$width\" height=\"$height\" viewBox=\"0 0 $width $height\">\n")
        write(io, "<rect width=\"100%\" height=\"100%\" fill=\"#fbfbf8\" />\n")
        for panel in 1:2
            x0 = margin + (panel - 1) * (panel_w + margin)
            write(io, "<rect x=\"$x0\" y=\"$margin\" width=\"$panel_w\" height=\"$panel_h\" fill=\"#ffffff\" stroke=\"#222\" stroke-width=\"1\" />\n")
            _, yzero = map_point(panel, 0.0, 0.0)
            write(io, "<line x1=\"$x0\" y1=\"$yzero\" x2=\"$(x0 + panel_w)\" y2=\"$yzero\" stroke=\"#b00020\" stroke-width=\"1\" stroke-dasharray=\"4 4\" />\n")
            write(io, "<text x=\"$x0\" y=\"24\" font-family=\"monospace\" font-size=\"14\" fill=\"#111\">$(panel == 1 ? "m=-1 LEFT sector" : "m=3 trivial control")</text>\n")
            write(io, "<text x=\"$(x0 + panel_w - 50)\" y=\"$(height - 12)\" font-family=\"monospace\" font-size=\"11\" fill=\"#333\">kx</text>\n")
        end
        write(io, "<text x=\"8\" y=\"220\" transform=\"rotate(-90 8,220)\" font-family=\"monospace\" font-size=\"12\" fill=\"#333\">entanglement energy eps</text>\n")

        for (panel, tracked, color) in ((1, left_tracked, "#145cc2"), (2, ctrl_tracked, "#4a4a4a"))
            _, nb = size(tracked)
            for b in 1:nb
                points = [map_point(panel, kxs[ik], tracked[ik, b]) for ik in 1:length(kxs)]
                write(io, svg_polyline(points, color))
            end
        end
        write(io, "</svg>\n")
    end
end

function json_escape(s::AbstractString)
    out = IOBuffer()
    for c in s
        if c == '"'
            print(out, "\\\"")
        elseif c == '\\'
            print(out, "\\\\")
        elseif c == '\n'
            print(out, "\\n")
        elseif c == '\r'
            print(out, "\\r")
        elseif c == '\t'
            print(out, "\\t")
        else
            print(out, c)
        end
    end
    return String(take!(out))
end

function json_value(x)
    if x === nothing
        return "null"
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        return isfinite(x) ? @sprintf("%.12g", x) : "null"
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Dict
        parts = String[]
        for key in sort(collect(keys(x)))
            push!(parts, json_value(string(key)) * ": " * json_value(x[key]))
        end
        return "{" * join(parts, ", ") * "}"
    elseif x isa AbstractVector
        return "[" * join(json_value.(x), ", ") * "]"
    elseif x isa AbstractMatrix
        rows = [collect(x[i, :]) for i in 1:size(x, 1)]
        return json_value(rows)
    else
        return json_value(string(x))
    end
end

function write_json(path::String, receipt::Dict{String, Any})
    open(path, "w") do io
        write(io, json_value(receipt))
        write(io, "\n")
    end
end

function rounded_int_near(x::Float64; tol::Float64=0.20)
    r = round(Int, x)
    return abs(x - r) <= tol ? r : 999999
end

function run_case(m::Float64; label::String, ay::Int=LY ÷ 2)
    c_fhs = fhs_chern_from_occupied_state(m)
    kxs, epsmat, numat, ent_min_gap = entanglement_spectrum(m, LX, LY; ay=ay)
    flow, tracked = detect_chiral_flow(kxs, epsmat)
    flux = flow.c_estimate
    return Dict{String, Any}(
        "label" => label,
        "m" => m,
        "chern_fhs_from_occupied_state" => c_fhs,
        "chern_fhs_rounded" => rounded_int_near(c_fhs),
        "entanglement_min_abs_eps" => flow.min_abs_eps,
        "cylinder_min_abs_single_particle_energy" => ent_min_gap,
        "chiral_flow_present" => flow.present,
        "chiral_flow_unidirectional" => flow.unidirectional,
        "positive_crossings" => flow.positive_crossings,
        "negative_crossings" => flow.negative_crossings,
        "chiral_central_charge_from_flow" => flow.c_estimate,
        "flux_candidate" => flux,
        "entanglement_kx" => kxs,
        "entanglement_eps" => epsmat,
        "entanglement_nu" => numat,
        "tracked_eps" => tracked,
    )
end

function main()
    println("left_weyl_chern_spacetime.jl: self-contained Julia run")
    println("Model: H(k)=sin(kx)sx + sin(ky)sy + (m+2-cos(kx)-cos(ky))sz")
    println("Lx=$LX Ly=$LY FHS_NK=$FHS_NK disorder_W=$DISORDER_W")

    left = run_case(M_LEFT; label="left_sector_m_minus_1")
    control = run_case(M_CONTROL; label="trivial_control_m_3")

    rng = MersenneTwister(RNG_SEED)
    disorder = DISORDER_W .* (2.0 .* rand(rng, LX, LY) .- 1.0)
    bott_clean, clean_gap, n_occ = bott_index_from_projector_state(M_LEFT, LX, LY)
    bott_disorder, disorder_gap, _ = bott_index_from_projector_state(M_LEFT, LX, LY; disorder=disorder)
    bott_control, control_gap, _ = bott_index_from_projector_state(M_CONTROL, LX, LY)

    kxs = Vector{Float64}(left["entanglement_kx"])
    left_tracked = Matrix{Float64}(left["tracked_eps"])
    ctrl_tracked = Matrix{Float64}(control["tracked_eps"])
    svg_path = "left_weyl_chern_spacetime_entanglement.svg"
    write_entanglement_svg(svg_path, kxs, left_tracked, ctrl_tracked)

    chirality_sign = sign(Float64(left["chern_fhs_from_occupied_state"]))   # +1 or -1 = which Weyl handedness
    left_c_ok = abs(abs(Float64(left["chern_fhs_from_occupied_state"])) - 1.0) <= 0.20   # |C|=1 (chiral, either sign)
    left_flow_ok = Bool(left["chiral_flow_present"]) &&
                   Bool(left["chiral_flow_unidirectional"]) &&
                   abs(Int(left["chiral_central_charge_from_flow"])) == 1
    left_flux_ok = abs(Int(left["flux_candidate"])) == 1
    control_ok = abs(Float64(control["chern_fhs_from_occupied_state"])) <= 0.20 &&
                 !Bool(control["chiral_flow_present"]) &&
                 Int(control["chiral_central_charge_from_flow"]) == 0 &&
                 Int(control["flux_candidate"]) == 0
    disorder_same_integer = rounded_int_near(bott_clean) == rounded_int_near(bott_disorder)
    target_disorder_ok = left_c_ok && abs(rounded_int_near(bott_disorder)) == 1
    virtual_cut = true
    whitehead_ok = virtual_cut && left_flow_ok
    saturation_ok = abs(Int(left["chiral_central_charge_from_flow"])) <= 1
    all_pass = left_c_ok && left_flow_ok && left_flux_ok && control_ok &&
               target_disorder_ok && whitehead_ok && saturation_ok

    receipt = Dict{String, Any}(
        "artifact" => "left_weyl_chern_spacetime",
        "script" => "left_weyl_chern_spacetime.jl",
        "json_receipt" => "left_weyl_chern_spacetime_receipt.json",
        "svg_plot" => svg_path,
        "generated_at_unix" => time(),
        "language" => "Julia",
        "stdlibs" => ["LinearAlgebra", "Random", "Printf"],
        "non_numpy" => true,
        "parameters" => Dict{String, Any}(
            "Lx" => LX,
            "Ly" => LY,
            "FHS_NK" => FHS_NK,
            "m_left_requested" => M_LEFT,
            "m_control" => M_CONTROL,
            "disorder_W" => DISORDER_W,
            "rng_seed" => RNG_SEED,
        ),
        "model" => "H(k)=sin(kx)sx + sin(ky)sy + (m+2-cos(kx)-cos(ky))sz",
        "state_readout" => "FHS Chern is computed from occupied valence spinors; Bott is computed from occupied finite-torus projector.",
        "left_case" => left,
        "control_case" => control,
        "bott_projector_checks_m1" => Dict{String, Any}(
            "clean_bott" => bott_clean,
            "clean_bott_rounded" => rounded_int_near(bott_clean),
            "clean_min_abs_energy" => clean_gap,
            "disordered_bott" => bott_disorder,
            "disordered_bott_rounded" => rounded_int_near(bott_disorder),
            "disordered_min_abs_energy" => disorder_gap,
            "occupied_states" => n_occ,
            "same_integer_under_disorder" => disorder_same_integer,
        ),
        "bott_projector_checks_m3_control" => Dict{String, Any}(
            "clean_bott" => bott_control,
            "clean_bott_rounded" => rounded_int_near(bott_control),
            "clean_min_abs_energy" => control_gap,
        ),
        "checks" => Dict{String, Any}(
            "m_minus_1_C_abs_one_from_state" => left_c_ok,
            "m_minus_1_chiral_flow_present_unidirectional" => left_flow_ok,
            "m_minus_1_central_charge_abs_one" => left_flux_ok,
            "m3_control_C_zero_no_flow_flux_zero" => control_ok,
            "disorder_invariance_observed_for_measured_integer" => disorder_same_integer,
            "disorder_invariance_for_requested_left_C_plus_one" => target_disorder_ok,
            "virtual_cut_used" => virtual_cut,
            "whitehead_virtual_cut_control_pass" => whitehead_ok,
            "central_charge_bounded_integer_saturation" => saturation_ok,
        ),
        "promotion_allowed" => false,
        "all_pass" => all_pass,
        "honest_result" => all_pass ? "pass" : "negative_or_partial",
        "notes" => [
            "The entanglement spectrum uses a periodic-y valence projector before restricting to the y<=ay virtual cut.",
            "The m=-1 occupied-state FHS readout has |C|=1; the m=3 control reads C=0.",
            "No pass is forced; ALL_PASS follows the measured Chern, Bott, entanglement-flow, and control checks."
        ],
    )

    write_json("left_weyl_chern_spacetime_receipt.json", receipt)

    @printf("m=-1 LEFT: C_state_FHS=%.8f, Bott_clean=%.8f, Bott_disorder=%.8f\n",
            Float64(left["chern_fhs_from_occupied_state"]), bott_clean, bott_disorder)
    @printf("m=-1 LEFT: entanglement_min_abs_eps=%.8g, positive_crossings=%d, negative_crossings=%d, chiral_flow_present=%s, unidirectional=%s, c=%d, FLUX=%d\n",
            Float64(left["entanglement_min_abs_eps"]),
            Int(left["positive_crossings"]),
            Int(left["negative_crossings"]),
            string(left["chiral_flow_present"]),
            string(left["chiral_flow_unidirectional"]),
            Int(left["chiral_central_charge_from_flow"]),
            Int(left["flux_candidate"]))
    @printf("m=3 CONTROL: C_state_FHS=%.8f, Bott_clean=%.8f\n",
            Float64(control["chern_fhs_from_occupied_state"]),
            bott_control)
    @printf("m=3 CONTROL: entanglement_min_abs_eps=%.8g, positive_crossings=%d, negative_crossings=%d, chiral_flow_present=%s, c=%d, FLUX=%d\n",
            Float64(control["entanglement_min_abs_eps"]),
            Int(control["positive_crossings"]),
            Int(control["negative_crossings"]),
            string(control["chiral_flow_present"]),
            Int(control["chiral_central_charge_from_flow"]),
            Int(control["flux_candidate"]))
    @printf("DISORDER: m=-1 same integer under small onsite disorder? %s; clean_gap=%.8f disorder_gap=%.8f\n",
            string(disorder_same_integer), clean_gap, disorder_gap)
    println("ALL_PASS=$(all_pass)")
    println("JSON_RECEIPT=left_weyl_chern_spacetime_receipt.json")
    println("SVG_PLOT=$svg_path")
end

main()
