#!/usr/bin/env julia

using LinearAlgebra

const Lx = 24
const Ly = 24
const PI64 = Float64(pi)
const TWO_PI = 2.0 * pi
const RECEIPT_PATH = joinpath(@__DIR__, "L4_terrain_octet_receipt.json")
const RESULTS_PATH = joinpath(@__DIR__, "L4_terrain_octet_results.json")

const SPIN_STRUCTURES = [
    (name = "PP", phi_x = 0.0, phi_y = 0.0),
    (name = "PA", phi_x = 0.0, phi_y = PI64),
    (name = "AP", phi_x = PI64, phi_y = 0.0),
    (name = "AA", phi_x = PI64, phi_y = PI64),
]

const FLUX_SECTORS = [
    (label = "C=+1", m = -1.0, expected_c = 1),
    (label = "C=-1", m = -3.0, expected_c = -1),
]

const CONTROL_M = 3.0
const CONTROL_EXPECTED_C = 0
const TOL = 1.0e-8

function hamiltonian(kx::Float64, ky::Float64, m::Float64)
    dx = sin(kx)
    dy = sin(ky)
    dz = m + 2.0 - cos(kx) - cos(ky)

    return Hermitian(ComplexF64[
        dz              dx - im * dy
        dx + im * dy    -dz
    ])
end

function occupied_state(kx::Float64, ky::Float64, m::Float64)
    eig = eigen(hamiltonian(kx, ky, m))
    idx = argmin(eig.values)
    v = eig.vectors[:, idx]
    return v / norm(v)
end

function normalized_link(a::Vector{ComplexF64}, b::Vector{ComplexF64})
    overlap = dot(a, b)
    mag = abs(overlap)
    if mag <= eps(Float64)
        error("zero occupied-state overlap in FHS link")
    end
    return overlap / mag
end

function chern_number(m::Float64, phi_x::Float64, phi_y::Float64)
    states = Array{Vector{ComplexF64}}(undef, Lx, Ly)

    for ix in 1:Lx, iy in 1:Ly
        kx = (TWO_PI * (ix - 1) + phi_x) / Lx
        ky = (TWO_PI * (iy - 1) + phi_y) / Ly
        states[ix, iy] = occupied_state(kx, ky, m)
    end

    ux = Array{ComplexF64}(undef, Lx, Ly)
    uy = Array{ComplexF64}(undef, Lx, Ly)

    for ix in 1:Lx, iy in 1:Ly
        ixp = ix == Lx ? 1 : ix + 1
        iyp = iy == Ly ? 1 : iy + 1
        ux[ix, iy] = normalized_link(states[ix, iy], states[ixp, iy])
        uy[ix, iy] = normalized_link(states[ix, iy], states[ix, iyp])
    end

    total_phase = 0.0
    for ix in 1:Lx, iy in 1:Ly
        ixp = ix == Lx ? 1 : ix + 1
        iyp = iy == Ly ? 1 : iy + 1
        plaquette = ux[ix, iy] * uy[ixp, iy] * inv(ux[ix, iyp]) * inv(uy[ix, iy])
        total_phase += angle(plaquette)
    end

    return total_phase / TWO_PI
end

function pass_integer(c::Float64, expected::Int)
    return abs(c - expected) <= TOL
end

function phase_label(phi::Float64)
    return iszero(phi) ? "0" : "pi"
end

function json_escape(s::AbstractString)
    escaped = replace(s, "\\" => "\\\\")
    escaped = replace(escaped, "\"" => "\\\"")
    escaped = replace(escaped, "\n" => "\\n")
    escaped = replace(escaped, "\r" => "\\r")
    escaped = replace(escaped, "\t" => "\\t")
    return escaped
end

function json_value(x)
    if x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        if isfinite(x)
            return string(x)
        else
            return "\"" * string(x) * "\""
        end
    elseif x isa NamedTuple
        parts = String[]
        for key in keys(x)
            push!(parts, json_value(String(key)) * ": " * json_value(getfield(x, key)))
        end
        return "{" * join(parts, ", ") * "}"
    elseif x isa AbstractVector
        return "[" * join(json_value.(x), ", ") * "]"
    else
        error("unsupported JSON value type: $(typeof(x))")
    end
end

function main()
    terrains = NamedTuple[]
    controls = NamedTuple[]

    for spin in SPIN_STRUCTURES, flux in FLUX_SECTORS
        c = chern_number(flux.m, spin.phi_x, spin.phi_y)
        push!(terrains, (
            spin_structure = spin.name,
            boundary_condition = spin.name,
            twist_phase_x = phase_label(spin.phi_x),
            twist_phase_y = phase_label(spin.phi_y),
            m = flux.m,
            flux_sector = flux.label,
            expected_c = flux.expected_c,
            measured_c = c,
            pass = pass_integer(c, flux.expected_c),
        ))
    end

    for spin in SPIN_STRUCTURES
        c = chern_number(CONTROL_M, spin.phi_x, spin.phi_y)
        push!(controls, (
            spin_structure = spin.name,
            boundary_condition = spin.name,
            twist_phase_x = phase_label(spin.phi_x),
            twist_phase_y = phase_label(spin.phi_y),
            m = CONTROL_M,
            expected_c = CONTROL_EXPECTED_C,
            measured_c = c,
            pass = pass_integer(c, CONTROL_EXPECTED_C),
        ))
    end

    spin_names = Set(t.name for t in SPIN_STRUCTURES)
    spin_twists = Set((t.phi_x, t.phi_y) for t in SPIN_STRUCTURES)
    spin_structure_count_pass =
        length(SPIN_STRUCTURES) == 4 &&
        spin_names == Set(["PP", "PA", "AP", "AA"]) &&
        spin_twists == Set([(0.0, 0.0), (0.0, PI64), (PI64, 0.0), (PI64, PI64)])

    terrain_count_pass = length(terrains) == 8
    terrain_chern_pass = all(t.pass for t in terrains)
    control_pass = length(controls) == 4 && all(t.pass for t in controls)
    all_pass = terrain_count_pass && terrain_chern_pass && spin_structure_count_pass && control_pass

    receipt = (
        kind = "L4_terrain_octet_receipt",
        script = "layers/L4_terrain_octet.jl",
        model = "Qi-Wu-Zhang H(k)=sin(kx)sx+sin(ky)sy+(m+2-cos(kx)-cos(ky))sz",
        lattice = (Lx = Lx, Ly = Ly),
        berry_method = "Fukui-Hatsugai-Suzuki occupied-state plaquette over shifted torus BZ",
        spin_structure_group = "Z2xZ2 = H^1(T^2; Z2)",
        spin_structure_count = length(SPIN_STRUCTURES),
        flux_sector_count = length(FLUX_SECTORS),
        terrain_count = length(terrains),
        control_count = length(controls),
        tolerance = TOL,
        checks = (
            terrain_count_pass = terrain_count_pass,
            terrain_chern_pass = terrain_chern_pass,
            spin_structure_count_pass = spin_structure_count_pass,
            control_pass = control_pass,
        ),
        all_pass = all_pass,
        terrains = terrains,
        control_m3 = controls,
    )

    for outpath in (RECEIPT_PATH, RESULTS_PATH)
        open(outpath, "w") do io
            write(io, json_value(receipt))
            write(io, "\n")
        end
    end

    println("FULL L4 TERRAIN OCTET")
    println("grid: Lx=$(Lx), Ly=$(Ly)")
    println("spin structures: PP, PA, AP, AA = Z2xZ2 = H^1(T^2; Z2)")
    println()
    println("8-terrain table")
    println(rpad("spin", 6), rpad("twist_x", 10), rpad("twist_y", 10), rpad("m", 8), "measured C")
    for t in terrains
        println(
            rpad(t.spin_structure, 6),
            rpad(t.twist_phase_x, 10),
            rpad(t.twist_phase_y, 10),
            rpad(string(t.m), 8),
            string(t.measured_c),
        )
    end

    println()
    println("kill-control: trivial m=3")
    println(rpad("spin", 6), rpad("twist_x", 10), rpad("twist_y", 10), rpad("m", 8), "measured C")
    for t in controls
        println(
            rpad(t.spin_structure, 6),
            rpad(t.twist_phase_x, 10),
            rpad(t.twist_phase_y, 10),
            rpad(string(t.m), 8),
            string(t.measured_c),
        )
    end

    println()
    println("receipt: $(RECEIPT_PATH)")
    println("ALL_PASS: $(all_pass)")
end

main()
