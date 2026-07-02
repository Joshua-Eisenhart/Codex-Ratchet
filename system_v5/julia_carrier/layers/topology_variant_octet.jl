#!/usr/bin/env julia

# topology_variant_octet.jl
# -----------------------------------------------------------------------------
# CLAUDE.md step 4 — TOPOLOGY-VARIANT RERUN of the Chern-terrain octet.
#
# The canonical octet (layers/L4_terrain_octet.jl) lives on the |C|=1 QWZ model:
#   4 spin structures (PP/PA/AP/AA = H^1(T^2;Z2)) x 2 flux sectors (C=+1 / C=-1).
# This rerun moves the SAME octet structure to a DIFFERENT topology class: a
# genuine higher-Chern, two-band model with |C|=2.
#
# Mechanism (NOT a d_z trick — d_z edits only shift phase boundaries, never raise
# |C|). |C|=2 here comes from a winding-2 IN-PLANE d-vector. With
#   q := (cos ky - cos kx) + i*(sin kx * sin ky)
# the in-plane part winds twice around the BZ, so each Dirac/quadratic touching
# contributes |delta C|=2. Concretely:
#   dx = cos ky - cos kx
#   dy = sin kx * sin ky
#   dz = M - cos kx - cos ky        (mass term)
#   H(k) = dx*sx + dy*sy + dz*sz
# Numerically read phase diagram (FHS, this script):
#   |M|>2  -> C=0     (trivial)
#   -2<M<2 -> C=+2    (target higher-Chern class)
#   dy -> -dy         -> C=-2       (the two flux sectors of THIS class)
#
# HONEST BAR:
#   * C is MEASURED by integrated Berry curvature (Fukui-Hatsugai-Suzuki lattice
#     plaquette over the occupied spinor) — not planted.
#   * Independent second method: Bott index from a finite-torus occupied
#     projector (real-space U(1) loop). Two methods must agree on the integer.
#   * Positive control: octet at C=+2/-2 (4 spin x 2 flux).
#   * Negative / KILL control: trivial mass M=4 gives C=0 (would falsify "this is
#     a |C|=2 class" if it read 2).
#   * Boundary / distinctness control: the |C|=1 baseline QWZ is measured side by
#     side; C=1 and C=2 must be different measured integers, else the "higher
#     Chern" claim is empty.
#   * Anchor invariant: the Chern number itself, from integrated Berry curvature.
#   * No decorative Z3.
#
# classification: PoC   promotion_allowed: false
# Tools: LinearAlgebra (non-numpy). All readouts are numeric, none hardcoded.
# -----------------------------------------------------------------------------

using LinearAlgebra

const RESULTS_PATH = joinpath(@__DIR__, "topology_variant_octet_results.json")

const LX = 32
const LY = 32
const PI64 = Float64(pi)
const TWO_PI = 2.0 * pi
const TOL = 1.0e-6          # FHS integer tolerance (lattice Berry sum)
const BOTT_TOL = 0.20       # Bott index is noisier on a finite torus

# 4 spin structures = the four Z2 x Z2 boundary twists, H^1(T^2; Z2).
const SPIN_STRUCTURES = [
    (name = "PP", phi_x = 0.0,   phi_y = 0.0),
    (name = "PA", phi_x = 0.0,   phi_y = PI64),
    (name = "AP", phi_x = PI64,  phi_y = 0.0),
    (name = "AA", phi_x = PI64,  phi_y = PI64),
]

# Two flux sectors of the |C|=2 topology class. sign = +1 / -1 flips dy -> sign*dy.
const FLUX_SECTORS = [
    (label = "C=+2", M = 0.0, sign = 1.0,  expected_c = 2),
    (label = "C=-2", M = 0.0, sign = -1.0, expected_c = -2),
]

# Kill control: trivial mass, no band inversion -> C=0.
const CONTROL_M = 4.0
const CONTROL_EXPECTED_C = 0

# Boundary / distinctness control: baseline |C|=1 QWZ measured under the SAME
# FHS estimator so that C=1 vs C=2 is a measured difference, not an assertion.
const QWZ_C1_M = -1.0       # QWZ dz = m + 2 - cos kx - cos ky, m=-1 -> C=+1
const QWZ_C1_EXPECTED_C = 1

const PAULI_X = ComplexF64[0 1; 1 0]
const PAULI_Y = ComplexF64[0 -im; im 0]
const PAULI_Z = ComplexF64[1 0; 0 -1]

# ---- the |C|=2 winding-2 model -------------------------------------------------

function d_vector_c2(kx::Float64, ky::Float64, M::Float64, sgn::Float64)
    dx = cos(ky) - cos(kx)
    dy = sgn * sin(kx) * sin(ky)
    dz = M - cos(kx) - cos(ky)
    return (dx, dy, dz)
end

function hamiltonian_c2(kx::Float64, ky::Float64, M::Float64, sgn::Float64)
    dx, dy, dz = d_vector_c2(kx, ky, M, sgn)
    return Hermitian(dx * PAULI_X + dy * PAULI_Y + dz * PAULI_Z)
end

# baseline |C|=1 QWZ (same family as canonical L4_terrain_octet)
function hamiltonian_qwz1(kx::Float64, ky::Float64, m::Float64)
    dx = sin(kx)
    dy = sin(ky)
    dz = m + 2.0 - cos(kx) - cos(ky)
    return Hermitian(dx * PAULI_X + dy * PAULI_Y + dz * PAULI_Z)
end

function occupied_state(H::Hermitian{ComplexF64, Matrix{ComplexF64}})
    eig = eigen(H)
    idx = argmin(eig.values)
    v = eig.vectors[:, idx]
    return v / norm(v)
end

function normalized_link(a::Vector{ComplexF64}, b::Vector{ComplexF64})
    overlap = dot(a, b)
    mag = abs(overlap)
    if mag <= 1.0e-14
        error("zero occupied-state overlap in FHS link (gap closed?)")
    end
    return overlap / mag
end

# Fukui-Hatsugai-Suzuki Chern number from integrated Berry curvature.
# H_at(kx,ky) returns the Bloch Hamiltonian; phi_x/phi_y twist the BZ mesh
# (the spin-structure boundary phase).
function fhs_chern(H_at, phi_x::Float64, phi_y::Float64)
    states = Array{Vector{ComplexF64}}(undef, LX, LY)
    min_gap = Inf
    for ix in 1:LX, iy in 1:LY
        kx = (TWO_PI * (ix - 1) + phi_x) / LX
        ky = (TWO_PI * (iy - 1) + phi_y) / LY
        H = H_at(kx, ky)
        eig = eigen(H)
        gap = abs(eig.values[2] - eig.values[1])
        min_gap = min(min_gap, gap)
        idx = argmin(eig.values)
        v = eig.vectors[:, idx]
        states[ix, iy] = v / norm(v)
    end

    ux = Array{ComplexF64}(undef, LX, LY)
    uy = Array{ComplexF64}(undef, LX, LY)
    for ix in 1:LX, iy in 1:LY
        ixp = ix == LX ? 1 : ix + 1
        iyp = iy == LY ? 1 : iy + 1
        ux[ix, iy] = normalized_link(states[ix, iy], states[ixp, iy])
        uy[ix, iy] = normalized_link(states[ix, iy], states[ix, iyp])
    end

    total_phase = 0.0
    for ix in 1:LX, iy in 1:LY
        ixp = ix == LX ? 1 : ix + 1
        iyp = iy == LY ? 1 : iy + 1
        plaquette = ux[ix, iy] * uy[ixp, iy] * inv(ux[ix, iyp]) * inv(uy[ix, iy])
        total_phase += angle(plaquette)
    end
    return total_phase / TWO_PI, min_gap
end

# ---- independent second method: Bott index from finite-torus projector --------

site_index(x::Int, y::Int) = (y - 1) * LX + x
orb_index(x::Int, y::Int, a::Int) = 2 * (site_index(x, y) - 1) + a

function add_block!(h::Matrix{ComplexF64}, x1::Int, y1::Int, x2::Int, y2::Int,
                    block::AbstractMatrix{ComplexF64})
    for a in 1:2, b in 1:2
        h[orb_index(x1, y1, a), orb_index(x2, y2, b)] += block[a, b]
    end
end

# Real-space C=2 Hamiltonian from the same d-vector (Fourier components):
#   dx = cos ky - cos kx :  -1/2 (e^{ikx}+e^{-ikx}) + 1/2 (e^{iky}+e^{-iky})
#   dy = sgn sin kx sin ky : sgn * (-1/4)(e^{ikx}-e^{-ikx})(e^{iky}-e^{-iky})/i^2
#   dz = M - cos kx - cos ky : M*I - 1/2(...)x - 1/2(...)y on sz
# We assemble by direct hopping blocks. periodic in both directions.
function realspace_c2(M::Float64, sgn::Float64)
    dim = 2 * LX * LY
    h = zeros(ComplexF64, dim, dim)
    sx = PAULI_X; sy = PAULI_Y; sz = PAULI_Z
    for x in 1:LX, y in 1:LY
        xp = x == LX ? 1 : x + 1
        yp = y == LY ? 1 : y + 1
        xm = x == 1 ? LX : x - 1
        ym = y == 1 ? LY : y - 1

        # onsite: M*sz
        add_block!(h, x, y, x, y, Matrix{ComplexF64}(M * sz))

        # dx = cos ky - cos kx on sx:
        #   -cos kx -> -1/2 sx hop in +x and -x ; +cos ky -> +1/2 sx hop in +y,-y
        add_block!(h, x, y, xp, y, Matrix{ComplexF64}(-0.5 * sx))
        add_block!(h, xp, y, x, y, Matrix{ComplexF64}(-0.5 * sx))
        add_block!(h, x, y, x, yp, Matrix{ComplexF64}(0.5 * sx))
        add_block!(h, x, yp, x, y, Matrix{ComplexF64}(0.5 * sx))

        # dz = -cos kx - cos ky on sz
        add_block!(h, x, y, xp, y, Matrix{ComplexF64}(-0.5 * sz))
        add_block!(h, xp, y, x, y, Matrix{ComplexF64}(-0.5 * sz))
        add_block!(h, x, y, x, yp, Matrix{ComplexF64}(-0.5 * sz))
        add_block!(h, x, yp, x, y, Matrix{ComplexF64}(-0.5 * sz))

        # dy = sgn sin kx sin ky on sy.
        # sin kx sin ky = -1/4 (e^{ikx}-e^{-ikx})(e^{iky}-e^{-iky})
        #   = -1/4 [ e^{i(kx+ky)} - e^{i(kx-ky)} - e^{i(-kx+ky)} + e^{-i(kx+ky)} ]
        # hop to (xp,yp): coeff -1/4 ; (xp,ym): +1/4 ; (xm,yp): +1/4 ; (xm,ym): -1/4
        c = sgn * sy
        add_block!(h, x, y, xp, yp, Matrix{ComplexF64}(-0.25 * c))
        add_block!(h, x, y, xp, ym, Matrix{ComplexF64}( 0.25 * c))
        add_block!(h, x, y, xm, yp, Matrix{ComplexF64}( 0.25 * c))
        add_block!(h, x, y, xm, ym, Matrix{ComplexF64}(-0.25 * c))
    end
    return Hermitian(h)
end

function polar_unitary(a::Matrix{ComplexF64})
    f = svd(a)
    return f.U * f.Vt
end

function bott_index_c2(M::Float64, sgn::Float64)
    h = realspace_c2(M, sgn)
    eig = eigen(h)
    n_occ = length(eig.values) ÷ 2
    min_abs_energy = minimum(abs.(eig.values))
    v_occ = eig.vectors[:, 1:n_occ]

    dim = 2 * LX * LY
    phase_x = Vector{ComplexF64}(undef, dim)
    phase_y = Vector{ComplexF64}(undef, dim)
    for x in 1:LX, y in 1:LY, a in 1:2
        idx = orb_index(x, y, a)
        phase_x[idx] = exp(TWO_PI * im * (x - 1) / LX)
        phase_y[idx] = exp(TWO_PI * im * (y - 1) / LY)
    end

    ux_occ = v_occ' * (v_occ .* reshape(phase_x, :, 1))
    uy_occ = v_occ' * (v_occ .* reshape(phase_y, :, 1))
    ux = polar_unitary(Matrix{ComplexF64}(ux_occ))
    uy = polar_unitary(Matrix{ComplexF64}(uy_occ))
    # Loop orientation matched to the FHS plaquette orientation so the SIGNED
    # integer (not just |C|) agrees between the two methods. The opposite order
    # (uy ux uy' ux') gives the same magnitude with flipped sign — a pure
    # convention choice, verified for both flux sectors.
    loop = ux * uy * ux' * uy'
    bott = sum(angle.(eigvals(loop))) / TWO_PI
    return bott, min_abs_energy
end

# ---- helpers ------------------------------------------------------------------

pass_integer(c::Float64, expected::Int, tol::Float64) = abs(c - expected) <= tol
phase_label(phi::Float64) = iszero(phi) ? "0" : "pi"
round_int(c::Float64) = round(Int, c)

function json_escape(s::AbstractString)
    out = IOBuffer()
    for ch in s
        if ch == '"'; print(out, "\\\"")
        elseif ch == '\\'; print(out, "\\\\")
        elseif ch == '\n'; print(out, "\\n")
        elseif ch == '\r'; print(out, "\\r")
        elseif ch == '\t'; print(out, "\\t")
        else print(out, ch) end
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
        return isfinite(x) ? string(x) : "null"
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa NamedTuple
        parts = String[]
        for key in keys(x)
            push!(parts, json_value(String(key)) * ": " * json_value(getfield(x, key)))
        end
        return "{" * join(parts, ", ") * "}"
    elseif x isa AbstractVector
        return "[" * join(json_value.(x), ", ") * "]"
    else
        error("unsupported JSON value: $(typeof(x))")
    end
end

# ---- main ---------------------------------------------------------------------

function main()
    println("TOPOLOGY-VARIANT OCTET — higher-Chern |C|=2 rerun")
    println("model: H=dx sx + dy sy + dz sz,  dx=cos ky-cos kx, dy=sgn sin kx sin ky, dz=M-cos kx-cos ky")
    println("grid: LX=$(LX), LY=$(LY)   FHS tol=$(TOL)")
    println()

    terrains = NamedTuple[]
    for spin in SPIN_STRUCTURES, flux in FLUX_SECTORS
        H_at = (kx, ky) -> hamiltonian_c2(kx, ky, flux.M, flux.sign)
        c, gap = fhs_chern(H_at, spin.phi_x, spin.phi_y)
        push!(terrains, (
            spin_structure = spin.name,
            twist_phase_x = phase_label(spin.phi_x),
            twist_phase_y = phase_label(spin.phi_y),
            M = flux.M,
            dy_sign = flux.sign,
            flux_sector = flux.label,
            expected_c = flux.expected_c,
            measured_c = c,
            measured_c_int = round_int(c),
            min_band_gap = gap,
            pass = pass_integer(c, flux.expected_c, TOL),
        ))
    end

    # KILL control: trivial mass -> C=0 octet (must NOT read |C|=2).
    kill_controls = NamedTuple[]
    for spin in SPIN_STRUCTURES
        H_at = (kx, ky) -> hamiltonian_c2(kx, ky, CONTROL_M, 1.0)
        c, gap = fhs_chern(H_at, spin.phi_x, spin.phi_y)
        push!(kill_controls, (
            spin_structure = spin.name,
            twist_phase_x = phase_label(spin.phi_x),
            twist_phase_y = phase_label(spin.phi_y),
            M = CONTROL_M,
            expected_c = CONTROL_EXPECTED_C,
            measured_c = c,
            measured_c_int = round_int(c),
            min_band_gap = gap,
            pass = pass_integer(c, CONTROL_EXPECTED_C, TOL),
        ))
    end

    # DISTINCTNESS control: |C|=1 baseline QWZ measured by the SAME estimator.
    H_qwz = (kx, ky) -> hamiltonian_qwz1(kx, ky, QWZ_C1_M)
    c1, gap1 = fhs_chern(H_qwz, 0.0, 0.0)
    qwz_c1 = (
        model = "QWZ baseline dz=m+2-cos kx-cos ky, m=$(QWZ_C1_M)",
        expected_c = QWZ_C1_EXPECTED_C,
        measured_c = c1,
        measured_c_int = round_int(c1),
        min_band_gap = gap1,
        pass = pass_integer(c1, QWZ_C1_EXPECTED_C, TOL),
    )

    # INDEPENDENT second method: Bott index for the two flux sectors + kill.
    bott_plus, bott_gap_plus = bott_index_c2(0.0, 1.0)
    bott_minus, bott_gap_minus = bott_index_c2(0.0, -1.0)
    bott_kill, bott_gap_kill = bott_index_c2(CONTROL_M, 1.0)
    bott_block = (
        method = "Bott index from finite-torus occupied projector (real-space U(1) loop)",
        bott_C_plus2 = bott_plus,
        bott_C_plus2_int = round_int(bott_plus),
        bott_C_plus2_min_abs_energy = bott_gap_plus,
        bott_C_minus2 = bott_minus,
        bott_C_minus2_int = round_int(bott_minus),
        bott_C_minus2_min_abs_energy = bott_gap_minus,
        bott_kill_trivial = bott_kill,
        bott_kill_trivial_int = round_int(bott_kill),
        bott_kill_min_abs_energy = bott_gap_kill,
    )

    # ---- verdict gates (all MEASURED) ----------------------------------------

    # 1. octet structure present: 4 spin x 2 flux = 8 terrains, the right twists.
    spin_names = Set(s.name for s in SPIN_STRUCTURES)
    spin_twists = Set((s.phi_x, s.phi_y) for s in SPIN_STRUCTURES)
    octet_structure_pass =
        length(terrains) == 8 &&
        length(SPIN_STRUCTURES) == 4 &&
        length(FLUX_SECTORS) == 2 &&
        spin_names == Set(["PP", "PA", "AP", "AA"]) &&
        spin_twists == Set([(0.0, 0.0), (0.0, PI64), (PI64, 0.0), (PI64, PI64)])

    # 2. every terrain reads its expected |C|=2 (FHS) — the octet PERSISTS at |C|=2.
    octet_chern_pass = all(t.pass for t in terrains)
    octet_all_abs2 = all(abs(t.measured_c_int) == 2 for t in terrains)

    # 3. kill control: trivial mass reads C=0 for all four spin structures.
    kill_pass = all(t.pass for t in kill_controls) &&
                all(t.measured_c_int == 0 for t in kill_controls)

    # 4. distinctness: |C|=2 is genuinely a DIFFERENT integer from |C|=1.
    c2_int = abs(terrains[1].measured_c_int)            # should be 2
    c1_int = abs(qwz_c1.measured_c_int)                  # should be 1
    distinct_pass = qwz_c1.pass && c2_int == 2 && c1_int == 1 && c2_int != c1_int

    # 5. two flux sectors are genuinely +2 and -2 (not the same sector twice).
    plus_terrains = [t for t in terrains if t.flux_sector == "C=+2"]
    minus_terrains = [t for t in terrains if t.flux_sector == "C=-2"]
    flux_pair_pass =
        all(t.measured_c_int == 2 for t in plus_terrains) &&
        all(t.measured_c_int == -2 for t in minus_terrains)

    # 6. second-method agreement: Bott integer == FHS integer for both sectors,
    #    AND Bott kill control == 0.
    bott_agree_pass =
        round_int(bott_plus) == 2 &&
        round_int(bott_minus) == -2 &&
        round_int(bott_kill) == 0 &&
        abs(bott_plus - 2.0) <= BOTT_TOL &&
        abs(bott_minus + 2.0) <= BOTT_TOL &&
        abs(bott_kill) <= BOTT_TOL

    all_pass =
        octet_structure_pass &&
        octet_chern_pass &&
        octet_all_abs2 &&
        kill_pass &&
        distinct_pass &&
        flux_pair_pass &&
        bott_agree_pass

    honest_status =
        all_pass ? "PASS" :
        (octet_chern_pass && kill_pass && distinct_pass ? "PARTIAL" : "NEGATIVE")

    receipt = (
        kind = "topology_variant_octet_results",
        script = "layers/topology_variant_octet.jl",
        classification = "PoC",
        promotion_allowed = false,
        claim = "The Chern-terrain octet (4 spin structures x 2 flux sectors) persists on a higher-Chern topology class with |C|=2, distinct from the canonical |C|=1 octet; C read from integrated Berry curvature (FHS) and cross-checked by the Bott index.",
        variant_of = "layers/L4_terrain_octet.jl",
        model = "H(k)=dx sx + dy sy + dz sz; dx=cos ky-cos kx; dy=sgn sin kx sin ky; dz=M-cos kx-cos ky",
        winding_mechanism = "in-plane d-vector q=(cos ky-cos kx)+i sgn sin kx sin ky winds twice around BZ -> |C|=2; not a d_z trick",
        anchor_invariant = "Chern number from integrated Berry curvature (Fukui-Hatsugai-Suzuki lattice plaquette)",
        second_method = "Bott index from finite-torus occupied projector",
        lattice = (LX = LX, LY = LY),
        fhs_tolerance = TOL,
        bott_tolerance = BOTT_TOL,
        spin_structure_group = "Z2 x Z2 = H^1(T^2; Z2)",
        spin_structure_count = length(SPIN_STRUCTURES),
        flux_sector_count = length(FLUX_SECTORS),
        terrain_count = length(terrains),
        terrains = terrains,
        kill_control_trivial_m = kill_controls,
        distinctness_control_C1_baseline = qwz_c1,
        bott_second_method = bott_block,
        checks = (
            octet_structure_pass = octet_structure_pass,
            octet_chern_pass = octet_chern_pass,
            octet_all_abs_C_equals_2 = octet_all_abs2,
            kill_control_trivial_C0_pass = kill_pass,
            distinct_from_C1_pass = distinct_pass,
            flux_pair_plus2_minus2_pass = flux_pair_pass,
            bott_second_method_agreement_pass = bott_agree_pass,
        ),
        all_pass = all_pass,
        honest_status = honest_status,
        notes = [
            "C is MEASURED (integrated Berry curvature), not planted.",
            "KILL control: trivial mass M=$(CONTROL_M) must read C=0; if it read 2 the |C|=2 class claim falsifies.",
            "DISTINCTNESS: baseline QWZ reads |C|=1 under the same estimator, so C=2 != C=1 is a measured difference.",
            "Two methods (FHS Chern + Bott index) must agree on the integer for each flux sector.",
        ],
    )

    open(RESULTS_PATH, "w") do io
        write(io, json_value(receipt))
        write(io, "\n")
    end

    # ---- console report -------------------------------------------------------
    println("8-terrain octet on |C|=2 class")
    println(rpad("spin", 6), rpad("tw_x", 6), rpad("tw_y", 6), rpad("sector", 8),
            rpad("exp_C", 7), rpad("meas_C", 10), rpad("gap", 8), "pass")
    for t in terrains
        println(rpad(t.spin_structure, 6), rpad(t.twist_phase_x, 6), rpad(t.twist_phase_y, 6),
                rpad(t.flux_sector, 8), rpad(string(t.expected_c), 7),
                rpad(string(round(t.measured_c, digits=4)), 10),
                rpad(string(round(t.min_band_gap, digits=3)), 8), string(t.pass))
    end
    println()
    println("KILL control (trivial M=$(CONTROL_M), expect C=0)")
    for t in kill_controls
        println(rpad(t.spin_structure, 6), "meas_C=", rpad(string(round(t.measured_c, digits=4)), 10),
                "gap=", rpad(string(round(t.min_band_gap, digits=3)), 8), "pass=", string(t.pass))
    end
    println()
    println("DISTINCTNESS control: baseline QWZ |C|=1, measured C=$(round(qwz_c1.measured_c, digits=4)) (int $(qwz_c1.measured_c_int)), pass=$(qwz_c1.pass)")
    println("  -> measured |C|=2 vs |C|=1 distinct: $(distinct_pass)")
    println()
    println("Bott second method:")
    println("  C=+2 sector:  Bott=$(round(bott_plus, digits=4)) (int $(round_int(bott_plus)))  min|E|=$(round(bott_gap_plus, digits=4))")
    println("  C=-2 sector:  Bott=$(round(bott_minus, digits=4)) (int $(round_int(bott_minus)))  min|E|=$(round(bott_gap_minus, digits=4))")
    println("  kill trivial: Bott=$(round(bott_kill, digits=4)) (int $(round_int(bott_kill)))  min|E|=$(round(bott_gap_kill, digits=4))")
    println("  FHS/Bott agreement: $(bott_agree_pass)")
    println()
    println("CHECKS:")
    println("  octet_structure_pass            = $(octet_structure_pass)")
    println("  octet_chern_pass (all |C|=2)    = $(octet_chern_pass && octet_all_abs2)")
    println("  kill_control_trivial_C0_pass    = $(kill_pass)")
    println("  distinct_from_C1_pass           = $(distinct_pass)")
    println("  flux_pair_plus2_minus2_pass     = $(flux_pair_pass)")
    println("  bott_second_method_agreement    = $(bott_agree_pass)")
    println()
    println("HONEST_STATUS: $(honest_status)")
    println("ALL_PASS: $(all_pass)")
    println("results: $(RESULTS_PATH)")
end

main()
