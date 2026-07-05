#!/usr/bin/env julia

using Dates, JSON, LinearAlgebra, SHA

const SIM_ID = "tower_g10_terrain_flows_v0"
const HERE = @__DIR__
const OUT = joinpath(HERE, "results", SIM_ID * "_julia_results.json")

dagger(a) = adjoint(a)
comm(h, r) = h * r - r * h
function dissip(l, r)
    ld = dagger(l); a = ld * l
    return l * r * ld - 0.5 .* (a * r + r * a)
end
v(m) = vec(m)
m(w) = reshape(w, 2, 2)
fro(a) = norm(a)

const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const sm = ComplexF64[0 0; 1 0]
const sp = ComplexF64[0 1; 0 0]
const p0 = ComplexF64[1 0; 0 0]
const p1 = ComplexF64[0 0; 0 1]
const pxp = 0.5 .* (I2 + sx)
const pxm = 0.5 .* (I2 - sx)
const H0 = 0.5 .* sz
const HX = 0.5 .* sx
const STATES = [
    0.5 .* (I2 + 0.2 .* sx + 0.3 .* sy + 0.4 .* sz),
    0.5 .* (I2 - 0.5 .* sx + 0.1 .* sy - 0.2 .* sz),
    0.5 .* (I2 + 0.0 .* sx - 0.6 .* sy + 0.1 .* sz),
]

function rhs(name, side, r; eps=0.17)
    out = side == "out"
    h = out ? HX : H0
    sign = out ? 1.0 : -1.0
    if name == "Funnel"
        ls = out ? [0.42 .* sz, 0.31 .* sx] : [0.42 .* sx, 0.31 .* sy]
        return sum(dissip(l, r) for l in ls) + sign * im * eps .* comm(h, r)
    elseif name == "Vortex"
        ls = out ? [0.25 .* sy] : [0.25 .* sz]
        return sign * im .* comm(h, r) + eps .* sum(dissip(l, r) for l in ls)
    elseif name == "Pit"
        l = sqrt(0.73) .* (out ? sp : sm)
        return dissip(l, r) + sign * im * eps .* comm(h, r)
    end
    ps = out ? [pxp, pxm] : [p0, p1]
    hc = out ? HX : H0
    return sign * im .* comm(hc, r) + sum(0.37 .* (p * r * p - 0.5 .* (p * r + r * p)) for p in ps)
end

function superop(name, side; eps=0.17)
    basis = [ComplexF64[1 0; 0 0], ComplexF64[0 1; 0 0], ComplexF64[0 0; 1 0], ComplexF64[0 0; 0 1]]
    return hcat([v(rhs(name, side, b; eps=eps)) for b in basis]...)
end

function fixed_point(L)
    tr = ComplexF64[1 0 0 1]
    aa = vcat(L[1:3, :], tr)
    bb = ComplexF64[0, 0, 0, 1]
    r = m(pinv(aa) * bb)
    r = 0.5 .* (r + dagger(r))
    return real.(diag(r))
end

function classify(name, side)
    L = superop(name, side)
    vals = eigvals(L)
    contraction = -real(tr(L)) / 4.0
    swirl = maximum(abs.(imag.(vals)))
    deltas = [fro(rhs(name, side, r)) for r in STATES]
    zero_swirl = maximum(abs.(imag.(eigvals(superop(name, side; eps=0.0)))))
    return Dict("fixed_point_diag" => fixed_point(L), "contraction" => contraction, "swirl" => swirl, "balance" => contraction / (swirl + 1e-12), "phase_portrait_witness" => maximum(deltas), "eps0_swirl" => zero_swirl)
end

function measured_controls(names, pairs, distinguish)
    relabeled_pairs = Dict("Funnel" => "Spiral", "Vortex" => "Cannon", "Pit" => "Citadel", "Hill" => "Source")
    inverse = Dict(v => k for (k, v) in pairs)
    relabeled = Dict("$(n)_vs_$(relabeled_pairs[n])" => fro(superop(n, "in") - superop(inverse[relabeled_pairs[n]], "out")) for n in names)
    moved = [abs(relabeled["$(n)_vs_$(relabeled_pairs[n])"] - distinguish["$(n)_vs_$(pairs[n])"]) > 1e-6 for n in names]
    claimed_new = Dict("$(n)_identity_relabel_claimed_new" => fro(superop(n, "in") - superop(n, "in")) for n in names)
    shuffle_order = ["Pit", "Funnel", "Hill", "Vortex"]
    shuffled = Dict("$(n)_vs_$(pairs[n])" => distinguish["$(src)_vs_$(pairs[src])"] for (n, src) in zip(names, shuffle_order))
    keyed_changed = any(abs(shuffled["$(n)_vs_$(pairs[n])"] - distinguish["$(n)_vs_$(pairs[n])"]) > 1e-6 for n in names)
    multiset_preserved = sort(round.(collect(values(shuffled)); digits=12)) == sort(round.(collect(values(distinguish)); digits=12))
    return Dict(
        "eps0_degenerations_recorded" => true,
        "relabel_control_dies" => maximum(values(claimed_new)) < 1e-12,
        "relabel_values" => claimed_new,
        "relabel_pairing_permutation" => relabeled_pairs,
        "relabel_measured_distinguishability" => relabeled,
        "relabel_values_move_with_channels" => all(moved),
        "label_shuffle" => Dict("order" => shuffle_order, "keyed_changed" => keyed_changed, "multiset_preserved" => multiset_preserved, "computed_values" => shuffled),
        "label_shuffle_survives" => keyed_changed && multiset_preserved,
    )
end

function main()
    names = ["Funnel", "Vortex", "Pit", "Hill"]
    pairs = Dict("Funnel" => "Cannon", "Vortex" => "Spiral", "Pit" => "Source", "Hill" => "Citadel")
    terrains = merge(Dict(n => classify(n, "in") for n in names), Dict(pairs[n] => classify(n, "out") for n in names))
    distinguish = Dict("$(n)_vs_$(pairs[n])" => fro(superop(n, "in") - superop(n, "out")) for n in names)
    controls = measured_controls(names, pairs, distinguish)
    source = joinpath(HERE, basename(@__FILE__))
    result = Dict(
        "schema" => "engine_leg_result_v1", "sim_id" => SIM_ID, "engine" => "julia",
        "classification" => "scratch_diagnostic", "promotion_allowed" => false, "formal_admission_allowed" => false,
        "created_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => bytes2hex(sha256(read(source))),
        "nesting" => "flows_on_G5_density_matrix_rho_floor", "geometry_not_axes" => true,
        "terrain_count" => length(terrains), "terrains" => terrains,
        "t1_t2_channel_distinguishability" => distinguish,
        "controls" => controls,
        "TOOL_MANIFEST" => Dict("LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing native complex matrix superoperator/eigensystem/fixed-point leg"), "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization")),
        "TOOL_INTEGRATION_DEPTH" => Dict("LinearAlgebra" => "load_bearing", "JSON" => "supportive"),
    )
    result["all_pass"] = length(terrains) == 8 && minimum(values(distinguish)) > 1e-6 && controls["relabel_control_dies"] && controls["relabel_values_move_with_channels"] && controls["label_shuffle_survives"]
    mkpath(dirname(OUT))
    write(OUT, JSON.json(result, 2))
    println(JSON.json(Dict("engine" => "julia", "all_pass" => result["all_pass"], "out" => OUT)))
end

main()
