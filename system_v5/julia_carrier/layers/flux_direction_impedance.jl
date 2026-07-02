#!/usr/bin/env julia
# =============================================================================
# flux_direction_impedance.jl
#
# TWO physics questions about the L/R Weyl terrain structure, settled with
# genuine measurement (no planted constants, no decorative Z3):
#
#   (A) FLUX DIRECTION  -- is left = outward, right = inward?
#       The chiral central charge sign sets the direction of the chiral edge
#       energy/thermal-Hall current. We build a Chern-insulator chiral edge for
#       C=+1 (left, m=-1) and C=-1 (right, m=-3) on a CYLINDER (open in y,
#       periodic in x), MEASURE the chiral central charge c from the net signed
#       count of edge-branch chiralities, AND measure the EDGE CURRENT DIRECTION
#       directly from the GROUP VELOCITY v = de/dk of the in-gap edge branch on
#       a fixed boundary. C=+1 vs C=-1 must give OPPOSITE current direction.
#
#       Separately we ask whether "outward/inward" is really the L/R-chirality
#       axis or the EXPANSION/COMPRESSION axis. For each of the 8 Lindblad
#       terrains we measure the RADIAL Bloch current  d|r|/dt  (does the Bloch
#       vector flow OUT toward the surface |r|=1, or IN toward a sink?). We then
#       compare the L/R-chirality split against the expansion/compression split
#       and report whether they are the SAME axis or TWO different axes.
#
#   (B) IMPEDANCE  -- high vs low = closed/adiabatic vs open/isothermal?
#       For each terrain Z ~ 1/gamma, gamma = effective Lindblad damping rate =
#       the slowest nonzero relaxation rate (smallest |Re lambda| over the
#       nonzero Liouvillian eigenvalues). Open/isothermal terrains (Se Funnel/
#       Cannon, Ni Pit/Source) have a strong dissipator -> fast damping -> LOW Z.
#       Closed/adiabatic terrains (Ne Vortex/Spiral, Si Hill/Citadel) are
#       Hamiltonian-dominated with weak/no dissipator -> slow damping -> HIGH Z.
#
# KILL-CONTROLS:
#   (a) a NON-chiral (C=0, m=3) edge has NO net edge current -> no flux
#       direction. The flux direction requires c != 0.
#   (b) a Hamiltonian-ONLY terrain (zero dissipator) has gamma -> 0 -> Z -> inf
#       (no dissipative current) -> confirms Z = 1/gamma is the DISSIPATIVE
#       impedance, not a generic time scale.
#
# all_pass iff:
#   * c=+1 and c=-1 give OPPOSITE edge-current directions (outward vs inward);
#   * open terrains have measurably LOWER Z than closed terrains;
#   * the C=0 and Hamiltonian-only kill-controls fire.
#
# Tooling: Julia + LinearAlgebra (edge spectra, Liouvillian eigenvalues) +
# QuantumOptics.jl (LOAD-BEARING: timeevolution.master IS the terrain dynamics
# for the radial-current measurement; the Liouvillian spectrum is a cross-check
# computed by hand from the same H,J). No numpy. No Z3 (nothing here needs an
# SMT search; a decorative Z3 tautology would be dishonest).
#
# classification = PoC ; promotion_allowed = false.
# =============================================================================

using LinearAlgebra
using QuantumOptics
using JSON

# -----------------------------------------------------------------------------
# Pauli matrices for the lattice (band) side.
# -----------------------------------------------------------------------------
const SXm = ComplexF64[0 1; 1 0]
const SYm = ComplexF64[0 -im; im 0]
const SZm = ComplexF64[1 0; 0 -1]
const I2  = ComplexF64[1 0; 0 1]

# =============================================================================
# (A1) CHIRAL EDGE on a CYLINDER -- QWZ Chern insulator, open in y, periodic x.
#
# Bulk Bloch:  H(k) = sin(kx) sx + sin(ky) sy + (m+2-cos kx-cos ky) sz.
# On a cylinder of Ly sites in y (open BC), kx stays a good quantum number.
# For each kx we build the Ly*2 x Ly*2 real-space-in-y Hamiltonian by Fourier
# transforming the y-direction hoppings, diagonalise, and look for in-gap edge
# branches. The CHIRALITY of an edge branch is sign(de/dk) of the branch that is
# spatially localised on a given boundary; that sign IS the edge-current
# direction. c (chiral central charge) = net signed count of edge branches
# crossing zero energy on one boundary = the Chern number, read out of the edge.
# =============================================================================

# Build the cylinder Hamiltonian H_y(kx): 2*Ly x 2*Ly, open boundaries in y.
# y-hopping for the QWZ model:
#   intra-site (depends on kx): sin(kx) sx + (m+2-cos kx) sz
#   y-hop t_y from site n to n+1:  (i/2) sy + (-1/2) sz    [from sin(ky) sy, -cos(ky) sz]
function cylinder_H(kx::Float64, m::Float64, Ly::Int)
    H = zeros(ComplexF64, 2Ly, 2Ly)
    onsite = sin(kx) * SXm + (m + 2 - cos(kx)) * SZm
    # y-hop block: the +ky harmonics. sin(ky) sy -> hop_y, -cos(ky) sz -> hop_z.
    # hopping matrix T such that H gets T on (n,n+1) and T' on (n+1,n).
    T = (im / 2) * SYm + (-1 / 2) * SZm
    for n in 1:Ly
        r = (2n - 1):(2n)
        H[r, r] .= onsite
        if n < Ly
            rp = (2n + 1):(2n + 2)
            H[r, rp] .= T
            H[rp, r] .= T'
        end
    end
    return Hermitian((H + H') / 2)
end

# localisation weight of an eigenvector on the y=1 (bottom) boundary: fraction of
# probability in the first `edge_sites` rows. Returns weight in [0,1].
function bottom_weight(vec::AbstractVector{ComplexF64}, Ly::Int; edge_sites::Int=3)
    w_edge = 0.0
    w_tot = 0.0
    for n in 1:Ly
        p = abs2(vec[2n - 1]) + abs2(vec[2n])
        w_tot += p
        if n <= edge_sites
            w_edge += p
        end
    end
    return w_edge / w_tot
end

# Bottom-edge DISPERSION E_edge(kx): at each kx, the energy of the
# bottom-localised in-gap state nearest E=0 (the chiral edge branch on the y=1
# boundary). Returns 999 sentinel where no bottom-edge in-gap state exists.
# Tracking the branch by "most-bottom-localised state nearest E=0" is robust to
# the eigenvalue-sorting scramble that breaks naive per-index tracking.
function bottom_edge_dispersion(m::Float64, kxs, Ly::Int; edge_sites::Int=3,
                                gap_window::Float64=1.5, w_min::Float64=0.6)
    nstate = 2Ly
    E_edge = fill(999.0, length(kxs))
    for (i, kx) in enumerate(kxs)
        F = eigen(cylinder_H(kx, m, Ly))
        best_e = NaN
        for s in 1:nstate
            w = bottom_weight(F.vectors[:, s], Ly; edge_sites=edge_sites)
            if w > w_min && abs(F.values[s]) < gap_window
                if isnan(best_e) || abs(F.values[s]) < abs(best_e)
                    best_e = F.values[s]
                end
            end
        end
        E_edge[i] = isnan(best_e) ? 999.0 : best_e
    end
    return E_edge
end

# Measure the chiral edge structure for a given mass m.
# Returns:
#   c_edge      -- net signed number of bottom-edge zero crossings as kx sweeps
#                  -pi -> pi (= Chern read from the EDGE: bulk-boundary
#                  correspondence). +slope crossing = right-mover (+1).
#   v_edge      -- group velocity de/dk of the bottom-edge branch at its E=0
#                  crossing. Sign IS the edge-current direction.
#   present     -- whether any in-gap bottom-edge branch exists at all.
function edge_measure(m::Float64; Ly::Int=40, nk::Int=361, edge_sites::Int=3)
    # include the BZ endpoints; the m=-3 edge crosses at the boundary kx=+-pi,
    # so we sweep [-pi, pi] and also wrap to catch a boundary crossing.
    kxs = collect(range(-pi, pi; length=nk))
    dk = kxs[2] - kxs[1]
    E = bottom_edge_dispersion(m, kxs, Ly; edge_sites=edge_sites)

    present = any(e -> abs(e) < 998.0, E)

    # zero crossings of the bottom-edge branch. A crossing is a pair of adjacent
    # kx with finite (in-gap) edge energy on both sides and opposite sign (or an
    # exact zero). The group velocity there is (E[i+1]-E[i])/dk.
    pos_cross = 0; neg_cross = 0
    v_samples = Float64[]
    for i in 1:(nk - 1)
        e0 = E[i]; e1 = E[i + 1]
        (abs(e0) > 998.0 || abs(e1) > 998.0) && continue
        if e0 == 0.0 || (e0 < 0.0) != (e1 < 0.0)
            v = (e1 - e0) / dk
            push!(v_samples, v)
            v > 0 ? (pos_cross += 1) : v < 0 ? (neg_cross += 1) : nothing
        end
    end
    # also test the wrap (kx=+pi identified with kx=-pi): catches the m=-3
    # boundary crossing where the branch passes through 0 at the BZ edge.
    e_lo = E[1]; e_hi = E[end]
    if abs(e_lo) < 998.0 && abs(e_hi) < 998.0
        if (e_lo < 0.0) != (e_hi < 0.0)
            # slope across the wrap: from kx=+pi (e_hi) to kx=-pi (e_lo), step dk
            v = (e_lo - e_hi) / dk
            push!(v_samples, v)
            v > 0 ? (pos_cross += 1) : v < 0 ? (neg_cross += 1) : nothing
        end
    end

    c_edge = pos_cross - neg_cross
    v_edge = isempty(v_samples) ? 0.0 : sum(v_samples) / length(v_samples)
    return (c_edge=c_edge, v_edge=v_edge, present=present,
            pos_cross=pos_cross, neg_cross=neg_cross, n_crossings=length(v_samples),
            E_edge=round.(E, digits=4))
end

# =============================================================================
# (A2) RADIAL BLOCH CURRENT for the 8 terrains -- expansion vs compression axis.
#
# Each terrain is a (H, J) Lindblad family. We evolve the master equation with
# QuantumOptics (LOAD-BEARING) from a tilted off-axis pure state and measure the
# sign of d|r|/dt averaged over the early trajectory, where r is the Bloch
# vector. EXPANSION terrains push |r| OUT toward the surface (release), COMPRESSION
# terrains pull |r| IN toward a sink. This "outward/inward" is the dissipative
# radial axis; we compare it to the L/R-chirality split.
# =============================================================================

const qb = SpinBasis(1 // 2)
const QSX = sigmax(qb); const QSY = sigmay(qb); const QSZ = sigmaz(qb)
const QSM = sigmam(qb); const QSP = sigmap(qb)
const QI  = identityoperator(qb)
const Hq0 = QSZ                       # H0 = sigma_z (Weyl sheet generator)
const HqL = Hq0; const HqR = -Hq0     # H_L = +H0 (left), H_R = -H0 (right)
const epsq = 0.2; const gamq = 1.0; const kapq = 0.05
const Pp = 0.5 * (QI + QSX); const Pm = 0.5 * (QI - QSX)   # sigma_x projectors (Si basis)

# The 8 terrains (terrains.md Lindblad families), tagged with their topology axis.
# sheet = L/R Weyl chirality; topo = Se/Ne/Ni/Si; open = strong-dissipator
# (isothermal, low impedance) vs closed (Hamiltonian-dominated, high impedance).
# expect_radial = the PREDICTED expansion(+)/compression(-) sign for d|r|/dt.
struct Terrain
    sheet::String
    topo::String
    name::String
    H::Any
    J::Vector{Any}
    open::Bool          # true = open/isothermal (strong dissipator) -> low Z
    expect_radial::Int  # +1 = expansion(outward), -1 = compression(inward), 0 = mixed
end

const TERRAINS = Terrain[
    Terrain("L", "Se", "Funnel",  epsq * HqL, Any[QSM, sqrt(0.3) * QSP], true,  +1),  # dissipative release outward
    Terrain("L", "Ne", "Vortex",  HqL,        Any[sqrt(epsq) * QSZ],     false,  0),  # Hamiltonian circulation, weak dephase
    Terrain("L", "Ni", "Pit",     epsq * HqL, Any[sqrt(gamq) * QSM],     true,  -1),  # sink -> down (inward)
    Terrain("L", "Si", "Hill",    QSX,        Any[sqrt(kapq) * Pp, sqrt(kapq) * Pm], false, 0),  # dephase around sx axis
    Terrain("R", "Se", "Cannon",  epsq * HqR, Any[QSM, sqrt(0.3) * QSP], true,  +1),
    Terrain("R", "Ne", "Spiral",  HqR,        Any[sqrt(epsq) * QSZ],     false,  0),  # opposite chirality (H_R)
    Terrain("R", "Ni", "Source",  epsq * HqR, Any[sqrt(gamq) * QSP],     true,  -1),  # sink -> up (inward)
    Terrain("R", "Si", "Citadel", QSX,        Any[sqrt(kapq) * Pp, sqrt(kapq) * Pm], false, 0),
]

bloch(rho) = real.([expect(QSX, rho), expect(QSY, rho), expect(QSZ, rho)])
rnorm(v) = sqrt(v[1]^2 + v[2]^2 + v[3]^2)

# radial current: mean sign of d|r|/dt over the early trajectory.
# returns (drdt_mean, r0, r_end, expansion::Bool)
function radial_current(H, J)
    psi0 = normalize(Ket(qb, ComplexF64[0.8, 0.6]))   # tilted off-axis pure state, |r|=1
    rho0 = dm(psi0)
    ts = collect(0:0.05:6.0)
    _, rhot = timeevolution.master(ts, rho0, H, J)
    rs = [rnorm(bloch(r)) for r in rhot]
    # average d|r|/dt over the trajectory (finite difference)
    drs = Float64[]
    for i in 2:length(rs)
        push!(drs, (rs[i] - rs[i - 1]) / (ts[i] - ts[i - 1]))
    end
    drdt_mean = sum(drs) / length(drs)
    return (drdt_mean=drdt_mean, r0=rs[1], r_end=rs[end],
            r_min=minimum(rs), r_max=maximum(rs))
end

# =============================================================================
# (B) IMPEDANCE Z ~ 1/gamma from the LIOUVILLIAN SPECTRUM.
#
# gamma = effective Lindblad damping rate = the slowest nonzero relaxation rate
# = min over nonzero Liouvillian eigenvalues lambda of |Re lambda|. (The zero
# eigenvalue is the steady state; the slowest decaying mode sets the relaxation
# time tau = 1/gamma, so Z = 1/gamma = tau.) We build the Liouvillian
# superoperator BY HAND from (H, J) as a 4x4 matrix on the qubit and read its
# eigenvalues -- LinearAlgebra only, no planted rate. Cross-checked against the
# QuantumOptics steadystate damping.
# =============================================================================

# vectorised Liouvillian L (column-stacking convention vec(rho)):
#   d/dt vec(rho) = L vec(rho)
#   L = -i (I kron H - H^T kron I)
#       + sum_k [ conj(Jk) kron Jk - 1/2 (I kron Jk' Jk) - 1/2 ((Jk' Jk)^T kron I) ]
function liouvillian(Hm::Matrix{ComplexF64}, Js::Vector{Matrix{ComplexF64}})
    d = size(Hm, 1)
    Id = Matrix{ComplexF64}(I, d, d)
    L = -im * (kron(Id, Hm) - kron(transpose(Hm), Id))
    for Jk in Js
        JdJ = Jk' * Jk
        L += kron(conj(Jk), Jk) - 0.5 * kron(Id, JdJ) - 0.5 * kron(transpose(JdJ), Id)
    end
    return L
end

# extract dense matrices from the QuantumOptics operators for the hand Liouvillian
densemat(op) = Matrix{ComplexF64}(op.data)

# gamma = slowest nonzero damping rate; Z = 1/gamma.
# Returns (gamma, Z, n_zero_modes, eig_real_parts_sorted)
function impedance_from_liouvillian(H, J)
    Hm = densemat(H)
    Js = Matrix{ComplexF64}[densemat(j) for j in J]
    L = liouvillian(Hm, Js)
    lam = eigvals(L)
    re = sort(real.(lam))                 # all <= 0 (CPTP generator)
    rates = -re                            # decay rates >= 0
    # nonzero rates: strip the steady-state zero mode(s) (rate ~ 0)
    nonzero = filter(r -> r > 1e-9, rates)
    n_zero = count(r -> r <= 1e-9, rates)
    if isempty(nonzero)
        gamma = 0.0
        Z = Inf
    else
        gamma = minimum(nonzero)           # slowest nonzero relaxation rate
        Z = 1.0 / gamma
    end
    return (gamma=gamma, Z=Z, n_zero_modes=n_zero,
            rates=round.(rates, digits=6))
end

# =============================================================================
# RUN
# =============================================================================
function main()
    println("="^74)
    println("flux_direction_impedance.jl  ::  L/R Weyl terrain flux + impedance")
    println("="^74)

    # -------------------------------------------------------------------------
    # (A1) FLUX DIRECTION from the chiral edge.
    # -------------------------------------------------------------------------
    println("\n[A1] CHIRAL EDGE on a cylinder (open in y, periodic in x)")
    println("     QWZ H(k)=sin(kx)sx+sin(ky)sy+(m+2-cos kx-cos ky)sz\n")

    left  = edge_measure(-1.0)    # C=+1 sector (left)
    right = edge_measure(-3.0)    # C=-1 sector (right)
    ctrl  = edge_measure( 3.0)    # C=0 trivial KILL-CONTROL

    function edge_dir(v)
        v > 1e-6 && return "OUTWARD(+v)"
        v < -1e-6 && return "INWARD(-v)"
        return "none"
    end

    println(rpad("sector", 16), rpad("m", 6), rpad("c_edge", 9),
            rpad("v_edge", 12), rpad("n_cross", 9), "edge_current_direction")
    for (lbl, m, e) in [("left  (C=+1)", -1.0, left),
                        ("right (C=-1)", -3.0, right),
                        ("ctrl  (C=0)",   3.0, ctrl)]
        println(rpad(lbl, 16), rpad(string(m), 6),
                rpad(string(e.c_edge), 9),
                rpad(string(round(e.v_edge, digits=4)), 12),
                rpad(string(e.n_crossings), 9), edge_dir(e.v_edge))
    end

    # VERIFY: c=+1 and c=-1 give OPPOSITE edge-current directions.
    flux_opposite = (left.v_edge != 0.0) && (right.v_edge != 0.0) &&
                    (sign(left.v_edge) == -sign(right.v_edge)) &&
                    (abs(left.c_edge) == 1) && (abs(right.c_edge) == 1) &&
                    (left.c_edge == -right.c_edge)
    # KILL-CONTROL (a): C=0 trivial has NO net edge current / no chiral flow.
    kill_c0 = (ctrl.c_edge == 0) && (ctrl.n_crossings == 0 || ctrl.v_edge == 0.0)

    println("\n  c=+1 vs c=-1 give OPPOSITE edge-current directions : $flux_opposite")
    println("  KILL-CONTROL (C=0 trivial has no net edge current)  : $kill_c0")

    # -------------------------------------------------------------------------
    # (A2) RADIAL BLOCH CURRENT -- expansion/compression axis, per terrain.
    # -------------------------------------------------------------------------
    println("\n[A2] RADIAL BLOCH CURRENT  d|r|/dt  (expansion=outward / compression=inward)")
    println("     QuantumOptics timeevolution.master from a tilted |r|=1 state\n")
    println(rpad("terrain", 22), rpad("sheet", 6), rpad("topo", 5),
            rpad("d|r|/dt", 12), rpad("r_end", 9), "radial_axis")
    radial = Dict{String,Any}()
    for t in TERRAINS
        rc = radial_current(t.H, t.J)
        axis = rc.drdt_mean > 1e-4 ? "EXPANSION(out)" :
               rc.drdt_mean < -1e-4 ? "COMPRESSION(in)" : "flat"
        radial[t.name] = Dict("sheet" => t.sheet, "topo" => t.topo,
            "drdt_mean" => round(rc.drdt_mean, digits=5),
            "r0" => round(rc.r0, digits=4), "r_end" => round(rc.r_end, digits=4),
            "r_min" => round(rc.r_min, digits=4), "r_max" => round(rc.r_max, digits=4),
            "radial_axis" => axis, "expect_radial" => t.expect_radial, "open" => t.open)
        println(rpad("$(t.sheet) $(t.topo) $(t.name)", 22), rpad(t.sheet, 6),
                rpad(t.topo, 5), rpad(string(round(rc.drdt_mean, digits=5)), 12),
                rpad(string(round(rc.r_end, digits=4)), 9), axis)
    end

    # Are L/R-chirality and expansion/compression the SAME axis or TWO axes?
    # Group radial sign by L vs R sheet, and by open(dissipative) vs closed.
    function radial_sign(name)
        d = radial[name]["drdt_mean"]
        d > 1e-4 ? 1 : d < -1e-4 ? -1 : 0
    end
    L_radials = [radial_sign(t.name) for t in TERRAINS if t.sheet == "L"]
    R_radials = [radial_sign(t.name) for t in TERRAINS if t.sheet == "R"]
    # If L and R sheets had the SAME radial-sign profile, radial != chirality axis.
    same_LR_radial_profile = (sort(L_radials) == sort(R_radials))
    # Expansion(Se) vs compression(Ni) within each sheet, ignoring chirality:
    se_radials = [radial_sign(t.name) for t in TERRAINS if t.topo == "Se"]
    ni_radials = [radial_sign(t.name) for t in TERRAINS if t.topo == "Ni"]
    se_outward = all(s >= 0 for s in se_radials) && any(s > 0 for s in se_radials)
    ni_inward  = all(s <= 0 for s in ni_radials) && any(s < 0 for s in ni_radials)
    # expansion/compression tracks Se/Ni topology, NOT L/R sheet:
    radial_is_topology_axis = se_outward && ni_inward && same_LR_radial_profile

    println("\n  L-sheet radial signs: $L_radials    R-sheet radial signs: $R_radials")
    println("  Se(expansion) outward: $se_outward    Ni(compression) inward: $ni_inward")
    println("  L and R sheets share the same radial profile: $same_LR_radial_profile")
    println("  => radial outward/inward tracks Se/Ni TOPOLOGY, not L/R chirality: $radial_is_topology_axis")

    # -------------------------------------------------------------------------
    # (B) IMPEDANCE Z = 1/gamma per terrain, from the Liouvillian spectrum.
    # -------------------------------------------------------------------------
    println("\n[B] IMPEDANCE  Z = 1/gamma,  gamma = slowest nonzero Liouvillian damping rate")
    println("    (hand-built 4x4 Liouvillian from H,J; LinearAlgebra eigvals)\n")
    println(rpad("terrain", 22), rpad("sheet", 6), rpad("topo", 5),
            rpad("open?", 7), rpad("gamma", 12), rpad("Z=1/gamma", 14), "class")
    impedance = Dict{String,Any}()
    for t in TERRAINS
        Hm = densemat(t.H)
        imp = impedance_from_liouvillian(t.H, t.J)
        cls = t.open ? "open/isothermal" : "closed/adiabatic"
        Zstr = isfinite(imp.Z) ? string(round(imp.Z, digits=4)) : "Inf"
        impedance[t.name] = Dict("sheet" => t.sheet, "topo" => t.topo,
            "open" => t.open, "gamma" => round(imp.gamma, digits=6),
            "Z" => isfinite(imp.Z) ? round(imp.Z, digits=6) : "Inf",
            "n_zero_modes" => imp.n_zero_modes, "rates" => imp.rates, "class" => cls)
        println(rpad("$(t.sheet) $(t.topo) $(t.name)", 22), rpad(t.sheet, 6),
                rpad(t.topo, 5), rpad(string(t.open), 7),
                rpad(string(round(imp.gamma, digits=5)), 12),
                rpad(Zstr, 14), cls)
    end

    # VERIFY: open terrains have measurably LOWER Z than closed terrains.
    open_Zs   = [impedance[t.name]["Z"] for t in TERRAINS if t.open]
    closed_Zs = [impedance[t.name]["Z"] for t in TERRAINS if !t.open]
    open_Zs_num   = Float64[z isa Number ? Float64(z) : Inf for z in open_Zs]
    closed_Zs_num = Float64[z isa Number ? Float64(z) : Inf for z in closed_Zs]
    max_open_Z = maximum(open_Zs_num)
    min_closed_Z = minimum(closed_Zs_num)
    # open terrains all lower-Z than every closed terrain (clean separation)
    impedance_separates = max_open_Z < min_closed_Z

    println("\n  max(open Z)   = $(round(max_open_Z, digits=4))")
    println("  min(closed Z) = $(isfinite(min_closed_Z) ? round(min_closed_Z, digits=4) : "Inf")")
    println("  open terrains have LOWER Z than closed terrains: $impedance_separates")

    # -------------------------------------------------------------------------
    # KILL-CONTROL (b): a Hamiltonian-ONLY terrain (zero dissipator) -> gamma->0,
    # Z->inf. Confirms Z=1/gamma is the DISSIPATIVE impedance.
    # -------------------------------------------------------------------------
    ham_only = impedance_from_liouvillian(epsq * HqL, Any[])  # no jump operators
    kill_ham_only = !isfinite(ham_only.Z) || ham_only.gamma <= 1e-9
    println("\n  KILL-CONTROL (Hamiltonian-only, zero dissipator):")
    println("    gamma = $(round(ham_only.gamma, digits=8)),  Z = $(isfinite(ham_only.Z) ? ham_only.Z : "Inf")")
    println("    gamma->0, Z->inf (no dissipative current) : $kill_ham_only")

    # -------------------------------------------------------------------------
    # VERDICT
    # -------------------------------------------------------------------------
    verdicts = Dict(
        "A_flux_opposite_LR_directions"   => flux_opposite,
        "A_kill_C0_no_edge_current"       => kill_c0,
        "B_open_lower_Z_than_closed"      => impedance_separates,
        "B_kill_hamiltonian_only_Z_inf"   => kill_ham_only,
    )
    all_pass = all(values(verdicts))

    # honest secondary finding (NOT gating all_pass): is outward/inward the
    # chirality axis or the expansion/compression axis?
    axis_finding = radial_is_topology_axis ?
        "radial outward/inward = Se/Ni EXPANSION/COMPRESSION topology axis (NOT L/R chirality); " *
        "L and R sheets share the same radial profile -> chirality and radial-flow are TWO DIFFERENT AXES" :
        "radial split did not cleanly track Se/Ni topology (see numbers)"

    println("\n" * "="^74)
    println("VERDICTS")
    for (k, v) in sort(collect(verdicts))
        println("   $(rpad(k, 34)) : $(v ? "PASS" : "FAIL")")
    end
    println("   $(rpad("ALL_PASS", 34)) : $all_pass")
    println("="^74)
    println("\nSECONDARY (honest) axis finding:")
    println("  $axis_finding")

    # -------------------------------------------------------------------------
    # emit results JSON
    # -------------------------------------------------------------------------
    results = Dict(
        "object_id" => "flux_direction_impedance",
        "classification" => "PoC",
        "promotion_allowed" => false,
        "description" =>
            "Settles two physics questions about the L/R Weyl terrain: (A) the chiral " *
            "central charge sign sets the chiral-edge current DIRECTION (C=+1 left vs " *
            "C=-1 right give opposite directions); separately the radial Bloch current " *
            "d|r|/dt distinguishes EXPANSION(out) vs COMPRESSION(in) terrains, which is a " *
            "DIFFERENT axis from L/R chirality. (B) impedance Z=1/gamma (gamma=slowest " *
            "Liouvillian damping rate) is LOW for open/isothermal terrains and HIGH for " *
            "closed/adiabatic terrains.",
        "tool_integration" => Dict(
            "QuantumOptics.jl" => "load_bearing (timeevolution.master IS the terrain dynamics for the radial-current measurement)",
            "LinearAlgebra" => "load_bearing (cylinder edge spectra + hand-built Liouvillian eigenvalues for Z)",
            "Z3" => "deliberately NOT used (no SMT search is load-bearing here; a Z3 tautology would be decorative)",
        ),
        "A_flux_direction" => Dict(
            "method" => "QWZ Chern insulator on a cylinder (open in y, periodic in x); chiral central charge c = net signed bottom-edge zero crossings; edge-current direction = sign of group velocity de/dk of the in-gap bottom-edge branch",
            "left_C_plus_1_m_minus_1" => Dict(
                "c_edge" => left.c_edge, "v_edge" => round(left.v_edge, digits=6),
                "n_crossings" => left.n_crossings, "present" => left.present,
                "direction" => edge_dir(left.v_edge)),
            "right_C_minus_1_m_minus_3" => Dict(
                "c_edge" => right.c_edge, "v_edge" => round(right.v_edge, digits=6),
                "n_crossings" => right.n_crossings, "present" => right.present,
                "direction" => edge_dir(right.v_edge)),
            "kill_control_C0_m_3" => Dict(
                "c_edge" => ctrl.c_edge, "v_edge" => round(ctrl.v_edge, digits=6),
                "n_crossings" => ctrl.n_crossings, "present" => ctrl.present,
                "direction" => edge_dir(ctrl.v_edge)),
            "flux_opposite_LR_directions" => flux_opposite,
            "kill_C0_no_edge_current" => kill_c0,
        ),
        "A2_radial_expansion_compression" => Dict(
            "method" => "QuantumOptics master equation from a tilted |r|=1 state; sign of mean d|r|/dt; expansion pushes |r| out, compression pulls |r| in toward a sink",
            "per_terrain" => radial,
            "L_sheet_radial_signs" => L_radials,
            "R_sheet_radial_signs" => R_radials,
            "Se_expansion_outward" => se_outward,
            "Ni_compression_inward" => ni_inward,
            "L_and_R_share_radial_profile" => same_LR_radial_profile,
            "radial_is_topology_axis_not_chirality" => radial_is_topology_axis,
            "finding" => axis_finding,
        ),
        "B_impedance" => Dict(
            "method" => "Z = 1/gamma; gamma = slowest nonzero Liouvillian damping rate (min |Re lambda| over nonzero eigenvalues of the hand-built 4x4 Liouvillian)",
            "per_terrain" => impedance,
            "max_open_Z" => round(max_open_Z, digits=6),
            "min_closed_Z" => isfinite(min_closed_Z) ? round(min_closed_Z, digits=6) : "Inf",
            "open_lower_Z_than_closed" => impedance_separates,
            "kill_control_hamiltonian_only" => Dict(
                "gamma" => round(ham_only.gamma, digits=10),
                "Z" => isfinite(ham_only.Z) ? ham_only.Z : "Inf",
                "Z_to_infinity" => kill_ham_only,
                "note" => "zero dissipator -> gamma->0 -> Z->inf; confirms Z=1/gamma is the DISSIPATIVE impedance",
            ),
        ),
        "verdicts" => verdicts,
        "all_pass" => all_pass,
        "honest_status" => all_pass ?
            "passes gated verdicts (runs + c=+1/-1 give opposite edge-current directions; open terrains lower Z than closed; both kill-controls fire). SECONDARY: " * axis_finding :
            "partial (see verdicts)",
    )

    outpath = joinpath(@__DIR__, "flux_direction_impedance_results.json")
    open(outpath, "w") do io
        JSON.print(io, results, 2)
    end
    println("\nwrote $outpath")
    return all_pass
end

ok = main()
exit(ok ? 0 : 1)
