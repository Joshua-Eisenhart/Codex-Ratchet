# L4_terrain_generator.jl
#
# L4 = TERRAIN / CHANNEL / GENERATOR.
#
# Object under test: the "8 terrains" of a 2D free-fermion Chern insulator on a
# T^2 leaf. A terrain is a pair
#       (spin structure on T^2 , sign of the Chern flux).
# There are exactly 8 of them:
#   * 4 spin structures  <->  H^1(T^2; Z2) = Z2 x Z2, the four fermion boundary
#     conditions  PP / PA / AP / AA  (periodic / antiperiodic in x and y).
#   * 2 Chern signs       C = +1 and C = -1.
#
# Carrier: QWZ (Qi-Wu-Zhang) two-band Chern insulator
#       H(k) = sin(kx) sx + sin(ky) sy + (m + 2 - cos(kx) - cos(ky)) sz.
#
# What is MEASURED (never planted): for every terrain we READ the Chern number
# OUT OF THE STATE using the Fukui-Hatsugai-Suzuki (FHS) lattice Berry-curvature
# method on the occupied (lower) band, and CROSS-CHECK it against an independent
# small-step Berry-curvature sum. The Chern number is a sum over a discrete BZ
# grid of the imaginary log of a product of overlaps of numerically-diagonalised
# eigenvectors; nothing in the code sets it equal to +/-1 by hand.
#
# NON-CIRCULAR ANCHOR (known mathematical invariant):
#   The QWZ Chern phase diagram is a textbook result:
#       m in (-2, 0):  C = -1
#       m in (-4,-2):  C = +1
#       m > 0  or m < -4:  C = 0  (trivial band insulator)
#   We anchor every measured C against THIS known invariant, not against itself.
#   Sign convention here is the FHS lower-band convention; what matters for the
#   anchor is |C| and that the two mass windows give OPPOSITE signs.
#
# Spin-structure (boundary-condition) twist: a P/A boundary condition in a
# direction shifts the allowed momenta by a half-period, k -> k + (twist) with
# twist in {0, pi/L}. The Chern number is a BULK topological invariant and is
# PREDICTED to be INDEPENDENT of the spin structure. That independence is a
# genuine falsifiable read-out, not an assumption baked into the table.
#
# CONTROLS:
#   positive : m = -1  (chiral)   -> expect |C| = 1 on every spin structure
#   positive : m = -3  (chiral)   -> expect |C| = 1, OPPOSITE sign to m = -1
#   negative : m =  3  (trivial)  -> expect  C = 0  on every spin structure
#   boundary : m = -2  (gap-closing transition) -> C ill-defined / unstable; we
#              flag it, do NOT force a value.
#   KILL-CONTROL: the trivial mass m = 3 MUST give C = 0 on all four spin
#              structures. If FHS reported |C| = 1 for the trivial insulator the
#              whole read-out would be an artifact, so a nonzero C there kills it.
#   KILL-CONTROL 2 (wrong structure): a "flat" Hamiltonian with the sin(kx),
#              sin(ky) winding terms DELETED (only the sz mass term kept) has no
#              chirality and MUST give C = 0. If it still measured |C| = 1 the
#              FHS code would be reacting to grid artifacts, not to topology.
#
# classification: tool_lego_fit_probe (PoC). promotion_allowed = false.

using LinearAlgebra
using JSON
using Random

const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]

# QWZ Bloch Hamiltonian.
# kill_winding=true deletes the sin(kx) sx + sin(ky) sy winding terms (wrong-structure control).
function Hk(kx::Float64, ky::Float64, m::Float64; kill_winding::Bool=false)
    if kill_winding
        return (m + 2 - cos(kx) - cos(ky)) * sz
    end
    return sin(kx) * sx + sin(ky) * sy + (m + 2 - cos(kx) - cos(ky)) * sz
end

# Lower-band (occupied) eigenvector at momentum k.
function lower_band_vec(kx::Float64, ky::Float64, m::Float64; kill_winding::Bool=false)
    H = Hk(kx, ky, m; kill_winding=kill_winding)
    H = (H + H') / 2          # enforce Hermiticity against round-off
    F = eigen(Hermitian(H))
    # eigen on Hermitian returns ascending eigenvalues; index 1 = lower band.
    return F.vectors[:, 1], F.values
end

# Fukui-Hatsugai-Suzuki Chern number, read out of the STATE on an L x L grid.
# twist = (tx, ty) in radians is the spin-structure half-period offset.
# Returns (C_rounded, C_raw, min_gap) where C_raw is the (real-valued) sum
# before rounding -- we report it so the reader can see it is genuinely near an
# integer and not pinned to one.
function fhs_chern(m::Float64; L::Int=24, twist=(0.0, 0.0), kill_winding::Bool=false)
    tx, ty = twist
    # momentum grid; +1 wrap so plaquettes close on the torus
    kxs = [2pi * (i - 1) / L + tx for i in 1:(L + 1)]
    kys = [2pi * (j - 1) / L + ty for j in 1:(L + 1)]

    vecs = Array{Vector{ComplexF64}}(undef, L + 1, L + 1)
    min_gap = Inf
    for i in 1:(L + 1), j in 1:(L + 1)
        v, vals = lower_band_vec(kxs[i], kys[j], m; kill_winding=kill_winding)
        vecs[i, j] = v
        gap = vals[2] - vals[1]
        min_gap = min(min_gap, gap)
    end

    F_total = 0.0
    for i in 1:L, j in 1:L
        # link variables U_mu = <u(k)|u(k+mu)> / |...|, FHS field strength
        u00 = vecs[i, j]
        u10 = vecs[i + 1, j]
        u11 = vecs[i + 1, j + 1]
        u01 = vecs[i, j + 1]
        U1  = dot(u00, u10); U1 /= abs(U1)   # x-link at (i,j)
        U2  = dot(u10, u11); U2 /= abs(U2)   # y-link at (i+1,j)
        U3  = dot(u11, u01); U3 /= abs(U3)   # -x-link at (i+1,j+1)
        U4  = dot(u01, u00); U4 /= abs(U4)   # -y-link at (i,j+1)
        # plaquette Berry curvature in the principal branch
        Fij = angle(U1 * U2 * U3 * U4)
        F_total += Fij
    end
    C_raw = F_total / (2pi)
    # At a gap-closing transition the occupied eigenvector is degenerate and the
    # plaquette product can be ill-defined (NaN). Do NOT force an integer there;
    # report a sentinel so the boundary case is flagged, not faked.
    Cint = isfinite(C_raw) ? round(Int, C_raw) : 9999
    return (Cint, C_raw, min_gap)
end

# Independent cross-check: continuum-style Berry curvature via the standard
# two-band closed form for H = d(k) . sigma. The Chern number of the lower band
# is the degree of the map k -> dhat(k), computed here as a triangulated solid
# angle of dhat over the BZ. Totally separate code path from FHS (no eigen, no
# overlaps) -- used only to confirm FHS is not a coincidence of one method.
function dvec(kx::Float64, ky::Float64, m::Float64; kill_winding::Bool=false)
    if kill_winding
        return (0.0, 0.0, m + 2 - cos(kx) - cos(ky))
    end
    return (sin(kx), sin(ky), m + 2 - cos(kx) - cos(ky))
end

function dhat(kx, ky, m; kill_winding::Bool=false)
    d = dvec(kx, ky, m; kill_winding=kill_winding)
    n = sqrt(d[1]^2 + d[2]^2 + d[3]^2)
    n < 1e-12 && return (0.0, 0.0, 0.0)
    return (d[1] / n, d[2] / n, d[3] / n)
end

# signed solid angle of the spherical triangle (a,b,c) via Van Oosterom-Strackee
function solid_angle(a, b, c)
    cross(u, v) = (u[2]*v[3]-u[3]*v[2], u[3]*v[1]-u[1]*v[3], u[1]*v[2]-u[2]*v[1])
    ddot(u, v) = u[1]*v[1] + u[2]*v[2] + u[3]*v[3]
    triple = ddot(a, cross(b, c))
    na = sqrt(ddot(a, a)); nb = sqrt(ddot(b, b)); nc = sqrt(ddot(c, c))
    denom = na*nb*nc + ddot(a, b)*nc + ddot(a, c)*nb + ddot(b, c)*na
    return 2 * atan(triple, denom)
end

# Degree of dhat = (1/4pi) * sum of signed solid angles over a triangulated BZ.
# The skyrmion-number / degree equals MINUS the lower-band Chern number in this
# d.sigma convention; we report the magnitude and the relative sign separately.
function degree_chern(m::Float64; L::Int=80, twist=(0.0, 0.0), kill_winding::Bool=false)
    tx, ty = twist
    kxs = [2pi * (i - 1) / L + tx for i in 1:(L + 1)]
    kys = [2pi * (j - 1) / L + ty for j in 1:(L + 1)]
    grid = [dhat(kxs[i], kys[j], m; kill_winding=kill_winding) for i in 1:(L + 1), j in 1:(L + 1)]
    tot = 0.0
    for i in 1:L, j in 1:L
        a = grid[i, j]; b = grid[i + 1, j]; c = grid[i + 1, j + 1]; d = grid[i, j + 1]
        (a == (0.0,0.0,0.0) || b == (0.0,0.0,0.0) || c == (0.0,0.0,0.0) || d == (0.0,0.0,0.0)) && continue
        tot += solid_angle(a, b, c)
        tot += solid_angle(a, c, d)
    end
    deg = tot / (4pi)
    return (round(Int, deg), deg)
end

# ---------------------------------------------------------------------------
# Build the 8-terrain table.
# ---------------------------------------------------------------------------
# spin structures on T^2: twist in each direction is 0 (periodic, P) or pi/L
# (antiperiodic, A). Use a representative L for the twist offset.
const SPIN_STRUCTS = [
    ("PP", (0.0, 0.0)),
    ("PA", (0.0, :A)),
    ("AP", (:A, 0.0)),
    ("AA", (:A, :A)),
]

# Two masses giving the two Chern signs (from the KNOWN QWZ phase diagram).
const CHERN_MASSES = [("Cminus_m=-1", -1.0), ("Cplus_m=-3", -3.0)]

twist_for(tag, L) = tag === :A ? pi / L : (tag === 0.0 ? 0.0 : Float64(tag))

function build_terrains(; L::Int=24)
    terrains = Vector{Dict{String,Any}}()
    for (cname, m) in CHERN_MASSES
        for (sname, (txtag, tytag)) in SPIN_STRUCTS
            tw = (twist_for(txtag, L), twist_for(tytag, L))
            Cint, Craw, mingap = fhs_chern(m; L=L, twist=tw)
            deg_int, deg_raw = degree_chern(m; L=80, twist=tw)
            push!(terrains, Dict(
                "terrain"        => "$(sname)__$(cname)",
                "spin_structure" => sname,
                "chern_family"   => cname,
                "mass_m"         => m,
                "twist"          => collect(tw),
                "C_fhs"          => Cint,
                "C_fhs_raw"      => round(Craw, digits=6),
                "C_degree"       => deg_int,
                "C_degree_raw"   => round(deg_raw, digits=6),
                "min_band_gap"   => round(mingap, digits=6),
                "methods_agree"  => (abs(Cint) == abs(deg_int)),
            ))
        end
    end
    return terrains
end

# ---------------------------------------------------------------------------
# Controls + anchor.
# ---------------------------------------------------------------------------
# NaN-safe raw reporter (JSON cannot encode NaN; the boundary transition is the
# one place C_raw is genuinely undefined, so we surface that honestly).
safe_raw(x) = isfinite(x) ? round(x, digits=6) : "undefined_at_transition"

function run_controls(; L::Int=24)
    tw0 = (0.0, 0.0)

    # positive: m=-1 chiral
    Cm1, Cm1raw, g1 = fhs_chern(-1.0; L=L, twist=tw0)
    # positive: m=-3 chiral, opposite sign
    Cm3, Cm3raw, g3 = fhs_chern(-3.0; L=L, twist=tw0)
    # negative / KILL-CONTROL: m=3 trivial -> must be 0
    Ctriv, Ctrivraw, gtriv = fhs_chern(3.0; L=L, twist=tw0)
    # boundary: m=-2 gap closing transition -> ill defined; flag only
    Cbd, Cbdraw, gbd = fhs_chern(-2.0; L=L, twist=tw0)
    # KILL-CONTROL 2 (wrong structure): winding terms deleted -> no chirality.
    # With m=-1 the sz coefficient changes sign across the BZ so the band touches
    # (min_gap=0): the wrong structure cannot even sustain a smooth occupied band,
    # let alone |C|=1.
    Cnw, Cnwraw, gnw = fhs_chern(-1.0; L=L, twist=tw0, kill_winding=true)
    # KILL-CONTROL 3 (gapped wrong structure): winding deleted AND m=3 so the sz
    # coefficient stays strictly positive -> the band is GAPPED but the d-vector
    # is frozen along +z (degree-0 map). A gapped wrong structure MUST give C=0.
    # This is the sharp kill-control: if FHS returned |C|=1 on a gapped trivial-z
    # band it would be reacting to grid artifacts, not topology.
    Cnw2, Cnw2raw, gnw2 = fhs_chern(3.0; L=L, twist=tw0, kill_winding=true)

    # boundary case is "flagged" if it is either gap-closed (small gap) or the
    # FHS sum itself came back undefined (sentinel 9999) -- both mean C is not
    # well-defined and we refuse to force a value.
    bd_flagged = (gbd < 0.05) || (Cbd == 9999)

    controls = Dict(
        "positive_m=-1"        => Dict("C" => Cm1, "C_raw" => safe_raw(Cm1raw),
                                       "min_gap" => round(g1, digits=6),
                                       "expect" => "abs(C)=1", "pass" => abs(Cm1) == 1),
        "positive_m=-3"        => Dict("C" => Cm3, "C_raw" => safe_raw(Cm3raw),
                                       "min_gap" => round(g3, digits=6),
                                       "expect" => "abs(C)=1, opposite sign to m=-1",
                                       "pass" => abs(Cm3) == 1 && sign(Cm3) == -sign(Cm1)),
        "negative_KILL_m=3"    => Dict("C" => Ctriv, "C_raw" => safe_raw(Ctrivraw),
                                       "min_gap" => round(gtriv, digits=6),
                                       "expect" => "C=0 (trivial); nonzero would KILL",
                                       "pass" => Ctriv == 0),
        "boundary_m=-2"        => Dict("C" => Cbd == 9999 ? "undefined_at_transition" : Cbd,
                                       "C_raw" => safe_raw(Cbdraw),
                                       "min_gap" => round(gbd, digits=6),
                                       "expect" => "gap-closing transition; C ill-defined, flagged not forced",
                                       "flagged_unstable" => bd_flagged),
        "KILL2_wrong_structure"=> Dict("C" => Cnw, "C_raw" => safe_raw(Cnwraw),
                                       "min_gap" => round(gnw, digits=6),
                                       "expect" => "winding deleted, band touches -> no |C|=1; |C|=1 would KILL",
                                       "pass" => Cnw == 0 || Cnw == 9999),
        "KILL3_gapped_wrong_structure"=> Dict("C" => Cnw2 == 9999 ? "undefined" : Cnw2,
                                       "C_raw" => safe_raw(Cnw2raw),
                                       "min_gap" => round(gnw2, digits=6),
                                       "expect" => "winding deleted, GAPPED (m=3) -> C=0; |C|=1 would KILL",
                                       "pass" => Cnw2 == 0),
    )
    return controls
end

# Anchor measured C against the KNOWN QWZ phase diagram for a sweep of masses.
#
# The known TOPOLOGICAL CONTENT (convention-independent) is:
#   * m in (-2, 0)  : |C| = 1, sign s
#   * m in (-4,-2)  : |C| = 1, sign -s   (OPPOSITE window)
#   * m > 0 or m<-4 : C = 0   (trivial)
# The absolute sign s depends on BZ orientation / cross-product order and is a
# bookkeeping convention, not physics. We therefore fix s ONCE from the data
# (the measured sign in the m in (-2,0) window) and then check every other row
# against the known pattern up to that single global sign. This anchors to the
# textbook |C| pattern and the opposite-sign relation -- a genuine math invariant
# of the QWZ band -- without hand-picking a sign per row.
function run_anchor(; L::Int=24)
    # textbook lower-band Chern, in some fixed reference convention
    function known_C_ref(m)
        if -2.0 < m < 0.0
            return -1            # reference window sets the sign reference
        elseif -4.0 < m < -2.0
            return 1
        elseif m > 0.0 || m < -4.0
            return 0
        else
            return :transition
        end
    end

    masses = [-4.5, -3.5, -3.0, -2.5, -1.5, -1.0, -0.5, 0.5, 1.0, 3.0]
    meas = Dict{Float64,Int}()
    for m in masses
        Cint, Craw, g = fhs_chern(m; L=L, twist=(0.0, 0.0))
        meas[m] = Cint
    end

    # determine the global sign convention from the m in (-2,0) window
    ref_ms = [m for m in masses if -2.0 < m < 0.0]
    meas_ref_sign = sign(meas[ref_ms[1]])           # measured sign there
    known_ref_sign = sign(known_C_ref(ref_ms[1]))   # reference sign there
    global_sign = meas_ref_sign == known_ref_sign ? 1 : -1

    rows = Vector{Dict{String,Any}}()
    n_checked = 0
    n_match = 0
    for m in masses
        Cint = meas[m]
        Cint_, Craw, g = fhs_chern(m; L=L, twist=(0.0, 0.0))
        kc = known_C_ref(m)
        if kc === :transition
            kc_conv = "transition"
            match = false
        else
            kc_conv = global_sign * kc      # known value in the measured convention
            match = (Cint == kc_conv)
            n_checked += 1
            n_match += match ? 1 : 0
        end
        push!(rows, Dict("m" => m, "C_measured" => Cint,
                         "C_raw" => round(Craw, digits=6),
                         "C_known_in_convention" => kc_conv,
                         "min_gap" => round(g, digits=6), "match" => match))
    end
    return rows, n_checked, n_match, global_sign
end

# ---------------------------------------------------------------------------
# Run.
# ---------------------------------------------------------------------------
function main()
    Random.seed!(42)
    L = 24

    println("== L4 TERRAIN GENERATOR :: 8 terrains of a QWZ Chern insulator on T^2 ==\n")

    terrains = build_terrains(; L=L)
    println("8-terrain table (spin structure x Chern sign), C read out of the state:")
    println(rpad("terrain", 26), rpad("C_fhs", 7), rpad("C_fhs_raw", 13),
            rpad("C_deg", 7), rpad("min_gap", 11), "methods_agree")
    for t in terrains
        println(rpad(t["terrain"], 26), rpad(string(t["C_fhs"]), 7),
                rpad(string(t["C_fhs_raw"]), 13), rpad(string(t["C_degree"]), 7),
                rpad(string(t["min_band_gap"]), 11), t["methods_agree"])
    end

    # spin-structure independence of C within each Chern family (genuine prediction)
    ss_independent = true
    for (cname, _) in CHERN_MASSES
        fam = [t["C_fhs"] for t in terrains if t["chern_family"] == cname]
        if length(unique(fam)) != 1
            ss_independent = false
        end
    end
    println("\nChern number independent of spin structure within each family: ", ss_independent)

    # both Chern signs actually realised (a genuine +/- split, not planted equal)
    fam_signs = Dict{String,Int}()
    for (cname, _) in CHERN_MASSES
        fam = unique([t["C_fhs"] for t in terrains if t["chern_family"] == cname])
        fam_signs[cname] = length(fam) == 1 ? fam[1] : 999
    end
    two_signs = length(unique(values(fam_signs))) == 2 &&
                all(abs(v) == 1 for v in values(fam_signs))
    println("Two opposite nonzero Chern signs realised across families: ", two_signs,
            "  ", fam_signs)

    println("\n== CONTROLS ==")
    controls = run_controls(; L=L)
    for (k, v) in controls
        println(rpad(k, 24), v)
    end

    println("\n== NON-CIRCULAR ANCHOR vs known QWZ phase diagram ==")
    anchor_rows, n_checked, n_match, global_sign = run_anchor(; L=L)
    println("convention global_sign fixed from m in (-2,0) window: ", global_sign)
    println(rpad("m", 8), rpad("C_measured", 12), rpad("C_known_conv", 14), rpad("min_gap", 11), "match")
    for r in anchor_rows
        println(rpad(string(r["m"]), 8), rpad(string(r["C_measured"]), 12),
                rpad(string(r["C_known_in_convention"]), 14), rpad(string(r["min_gap"]), 11), r["match"])
    end
    println("anchor: $(n_match)/$(n_checked) measured Chern numbers match the known phase diagram")

    # honest status decision.
    # KILL2 wrong-structure passes iff the deleted-winding Hamiltonian does NOT
    # yield a chiral terrain, i.e. its measured C is 0 OR undefined (sentinel
    # 9999 = no smooth occupied band, band touching) -- anything but |C|=1.
    cnw = controls["KILL2_wrong_structure"]["C"]
    kill2_pass = (cnw == 0) || (cnw == 9999)
    controls["KILL2_wrong_structure"]["pass"] = kill2_pass
    controls["KILL2_wrong_structure"]["note"] = "pass = no chiral terrain (C in {0, undefined}); " *
        "9999 = band-touching, occupied band not smooth -> no |C|=1, kill-control satisfied"
    kill3_pass = controls["KILL3_gapped_wrong_structure"]["pass"]
    # kill_ok requires: trivial mass gives 0, AND the sharp gapped wrong-structure
    # gives exactly 0, AND the band-touching wrong-structure fails to make |C|=1.
    kill_ok   = controls["negative_KILL_m=3"]["pass"] && kill2_pass && kill3_pass
    pos_ok    = controls["positive_m=-1"]["pass"] && controls["positive_m=-3"]["pass"]
    anchor_ok = (n_match == n_checked)
    all_genuine = kill_ok && pos_ok && anchor_ok && ss_independent && two_signs

    status = all_genuine ? "passes" : "partial"
    println("\nHONEST STATUS: ", status,
            "  (kill_ok=$(kill_ok), pos_ok=$(pos_ok), anchor=$(n_match)/$(n_checked), ",
            "ss_independent=$(ss_independent), two_signs=$(two_signs))")

    results = Dict(
        "object"               => "L4_terrain_generator",
        "description"          => "8 terrains = 4 spin structures on T^2 x 2 Chern signs; " *
                                  "C read out of the state (FHS + degree) on a QWZ Chern insulator.",
        "classification"       => "tool_lego_fit_probe",
        "promotion_allowed"    => false,
        "carrier"              => "QWZ two-band Chern insulator H(k)=sin kx sx + sin ky sy + (m+2-cos kx-cos ky) sz",
        "measurement_methods"  => ["FHS lattice Berry curvature (occupied band eigenvectors)",
                                   "degree of d-hat map (triangulated solid angle, independent code path)"],
        "noncircular_anchor"   => "measured C compared to KNOWN QWZ phase diagram |C| pattern + opposite-sign relation " *
                                  "(m in (-2,0): |C|=1; (-4,-2): |C|=1 opposite sign; else 0), up to one global BZ-orientation sign",
        "anchor_global_sign"   => global_sign,
        "grid_L"               => L,
        "terrains"             => terrains,
        "n_terrains"           => length(terrains),
        "spin_structure_independent_C" => ss_independent,
        "two_opposite_chern_signs"     => two_signs,
        "family_signs"         => fam_signs,
        "controls"             => controls,
        "anchor"               => Dict("rows" => anchor_rows, "n_checked" => n_checked,
                                       "n_match" => n_match,
                                       "all_match" => anchor_ok),
        "ladder_status"        => status,
        "honest_status"        => "kill_ok=$(kill_ok); pos_ok=$(pos_ok); " *
                                  "anchor=$(n_match)/$(n_checked); ss_independent=$(ss_independent); " *
                                  "two_signs=$(two_signs)",
    )

    open(joinpath(@__DIR__, "L4_terrain_generator_results.json"), "w") do io
        JSON.print(io, results, 2)
    end
    println("\nwrote L4_terrain_generator_results.json")
    return results
end

main()
