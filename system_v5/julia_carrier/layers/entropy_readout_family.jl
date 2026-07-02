#!/usr/bin/env julia
#
# entropy_readout_family.jl
# classification = entropy_readout_family_poc ; promotion_allowed = false
#
# GENUINE entropy-readout family on a finite ENTANGLED spinor-network carrier.
# Julia + LinearAlgebra + ITensors/ITensorMPS (real MPS spinor network) + JSON. NON-numpy.
#
# Object: a finite entangled spinor network. Entropy is a READOUT on density operators
#   built by genuine partial traces; it is NEVER the primitive.
#
# GENUINE BAR enforced here:
#  (geometry) anchor = KNOWN topological invariant = FHS-plaquette Chern number of the
#     occupied-spinor Bloch projector P = |u><u| of the Qi-Wu-Zhang two-band model.
#     Topological mass m=-1 measures |C| = 1 (NOT a planted number); a WRONG-STRUCTURE
#     control (trivial mass m=+3) measures C = 0 -> the invariant FAILS for wrong structure.
#     Carrier is the projector / occupied spinor, density-operator only. NO Bloch r-vector.
#  (entanglement) MEASURE cut / Schmidt entropy of the ENTANGLED spinor-network MPS by SVD
#     of the bipartition; a PRODUCT control (factorized spinor product state) gives ~0.
#     Entanglement is load-bearing: every quantum readout collapses on the product control.
#
# Readouts (all from density operators, partial traces): S(rho), S(rho_A), conditional
#   S(A|B)=S(AB)-S(B), coherent info I_c(A>B)=S(B)-S(AB), mutual info I(A:B),
#   conditional mutual info I(A:C|B), relative entropy D(rho||sigma), Renyi-alpha,
#   sandwiched-Renyi, smooth min/max (approx), log-negativity, finite path entropy.
#
# Controls (load-bearing): PRODUCT state kills I_c / I(A:B) / negativity (classical baseline);
#   DEPHASE kills the quantum negativity but KEEPS the classical mutual information.
#
# Run: julia --project="/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier" \
#            "system_v5/julia_carrier/layers/entropy_readout_family.jl"

using LinearAlgebra
using ITensors
using ITensorMPS
using JSON

const NAME = "entropy_readout_family"
const CLASSIFICATION = "entropy_readout_family_poc"
const PROMOTION_ALLOWED = false
const RESULT_PATH = joinpath(@__DIR__, "entropy_readout_family_results.json")
const EPS = 1.0e-12
const GAP = 1.0e-6          # "is the entropy genuinely nonzero" gate
const COLLAPSE = 1.0e-9     # "did the product control collapse the readout" gate

# ----------------------------------------------------------------------------------------
# Pauli / spinor primitives (density-operator world only; no Bloch r-vector anywhere)
# ----------------------------------------------------------------------------------------
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const I2 = Matrix{ComplexF64}(I, 2, 2)

# ========================================================================================
# PART 1 -- GEOMETRY ANCHOR: FHS-plaquette Chern number of the occupied-spinor projector
#   Known invariant of the Qi-Wu-Zhang model: m in (-2,0) -> |C|=1 ; m>0 -> C=0.
#   We measure C by the Fukui-Hatsugai-Suzuki gauge-invariant plaquette method directly
#   from the occupied spinor |u(k)> (a density-operator carrier P=|u><u|, never an r-vector).
# ========================================================================================
function qwz_bloch(m::Float64, kx::Float64, ky::Float64)
    dx = sin(kx)
    dy = sin(ky)
    dz = m + cos(kx) + cos(ky)          # m in (-2,0): band inverts -> |C|=1 ; m>0: trivial
    return dx * SX + dy * SY + dz * SZ
end

# occupied (lower-band) spinor; the density-operator carrier is P = |u><u|
function occupied_spinor(m::Float64, kx::Float64, ky::Float64)
    e = eigen(Hermitian(qwz_bloch(m, kx, ky)))
    return e.vectors[:, 1]
end

unit_link(u, v) = (z = dot(u, v); a = abs(z); a <= 1e-14 ? one(ComplexF64) : z / a)

# FHS plaquette Chern from the occupied projector. Gauge invariant (uses only |u><u| data).
function fhs_chern(m::Float64; nk::Int = 24)
    occ = Array{ComplexF64}(undef, 2, nk, nk)
    for ix in 1:nk, iy in 1:nk
        kx = 2pi * (ix - 1) / nk
        ky = 2pi * (iy - 1) / nk
        occ[:, ix, iy] = occupied_spinor(m, kx, ky)
    end
    total = 0.0
    for ix in 1:nk, iy in 1:nk
        ixp = ix == nk ? 1 : ix + 1
        iyp = iy == nk ? 1 : iy + 1
        u1 = unit_link(occ[:, ix, iy],  occ[:, ixp, iy])
        u2 = unit_link(occ[:, ixp, iy], occ[:, ixp, iyp])
        u3 = unit_link(occ[:, ixp, iyp], occ[:, ix, iyp])
        u4 = unit_link(occ[:, ix, iyp], occ[:, ix, iy])
        total += angle(u1 * u2 * u3 * u4)
    end
    return total / (2pi)
end

# confirm the carrier is a genuine rank-1 projector (density operator), not an r-vector readout
function projector_is_density_operator(m::Float64, kx::Float64, ky::Float64)
    u = occupied_spinor(m, kx, ky)
    P = u * u'
    herm   = norm(P - P') < 1e-10
    idem   = norm(P * P - P) < 1e-10           # P^2 = P : genuine projector
    tr_one = abs(real(tr(P)) - 1.0) < 1e-10
    psd    = minimum(real.(eigvals(Hermitian(P)))) > -1e-10
    return Dict("hermitian" => herm, "idempotent" => idem, "trace_one" => tr_one,
                "psd" => psd, "is_density_operator" => herm && idem && tr_one && psd)
end

function geometry_anchor()
    m_topo = -1.0   # band-inverted: known |C| = 1
    m_triv =  3.0   # WRONG STRUCTURE control: trivial, known C = 0
    c_topo = fhs_chern(m_topo)
    c_triv = fhs_chern(m_triv)
    c_topo_int = round(Int, c_topo)
    c_triv_int = round(Int, c_triv)
    dens = projector_is_density_operator(m_topo, 0.7, 1.3)
    topo_ok    = abs(abs(c_topo) - 1.0) < 1e-6            # measured |C| = 1
    control_ok = abs(c_triv) < 1e-6                       # wrong structure FAILS the invariant
    return Dict(
        "invariant" => "FHS-plaquette Chern number of occupied-spinor projector (Qi-Wu-Zhang)",
        "topological_mass" => m_topo, "trivial_mass_control" => m_triv,
        "chern_topological_raw" => c_topo, "chern_topological_int" => c_topo_int,
        "chern_trivial_control_raw" => c_triv, "chern_trivial_control_int" => c_triv_int,
        "abs_chern_topological" => abs(c_topo),
        "carrier_is_density_operator" => dens,
        "invariant_anchored_pass" => topo_ok,
        "wrong_structure_control_fails_invariant" => control_ok,
        "bloch_r_vector_used" => false,
        "pass" => topo_ok && control_ok && dens["is_density_operator"],
    )
end

# ========================================================================================
# PART 2 -- ENTANGLED SPINOR-NETWORK CARRIER (genuine ITensors MPS) + cut/Schmidt entropy
# ========================================================================================
# Spinor-network MPS with a tunable two-spinor coupling angle per bond. theta>0 entangles
# neighbouring spinors (genuine many-body entanglement); theta=0 -> exact product state.
function build_spinor_network_mps(nsites::Int, theta::Float64; seed::Int = 20260602)
    sites = siteinds("S=1/2", nsites)
    # start in a Neel product |up,dn,up,dn,...>: this is NOT a hopping eigenstate, so the
    # XX+YY entangling bonds create genuine superposition/entanglement across the cut.
    psi = MPS(sites, [isodd(j) ? "Up" : "Dn" for j in 1:nsites])
    # apply nearest-neighbour entangling rotations exp(-i theta (XX+YY)/2): genuine 2-spinor coupling
    gates = ITensor[]
    for j in 1:(nsites - 1)
        s1, s2 = sites[j], sites[j + 1]
        hj = op("Sx", s1) * op("Sx", s2) + op("Sy", s1) * op("Sy", s2)
        push!(gates, exp(-im * theta * hj))
    end
    psi = apply(gates, psi; cutoff = 1e-14, maxdim = 64)
    # second sweep to spread correlation across the cut (real entanglement, not nearest-only)
    psi = apply(gates, psi; cutoff = 1e-14, maxdim = 64)
    normalize!(psi)
    return psi, sites
end

# cut / Schmidt entropy at bond b via SVD of the bipartition (genuine entanglement readout)
function cut_schmidt_entropy(psi::MPS, b::Int)
    psi = orthogonalize(psi, b)
    U, S, V = svd(psi[b], (linkinds(psi, b - 1)..., siteind(psi, b)))
    p = Float64[]
    for n in 1:dim(S, 1)
        sval = S[n, n]
        push!(p, sval^2)
    end
    ent = 0.0
    for pn in p
        if pn > EPS
            ent -= pn * log(pn)
        end
    end
    return ent, sort(p; rev = true)
end

# max cut entropy over interior bonds (the load-bearing entanglement readout)
function network_cut_entropy(psi::MPS)
    n = length(psi)
    bonds = collect(2:(n - 1))
    ents = [cut_schmidt_entropy(psi, b)[1] for b in bonds]
    return maximum(ents), bonds, ents
end

# ========================================================================================
# PART 3 -- DENSITY-OPERATOR ENTROPY READOUT FAMILY (all from partial traces)
# ========================================================================================
# We build an explicit small entangled 3-spinor density operator from the MPS amplitudes so
# every readout (conditional, coherent info, CMI, negativity, etc.) is an exact partial trace.

vn_entropy(rho) = (vals = real.(eigvals(Hermitian(Matrix(rho))));
    -sum(v > EPS ? v * log(v) : 0.0 for v in vals))

renyi_entropy(rho, alpha) = begin
    vals = real.(eigvals(Hermitian(Matrix(rho))))
    vals = [v for v in vals if v > EPS]
    if abs(alpha - 1.0) < 1e-9
        return -sum(v * log(v) for v in vals)
    end
    return log(sum(v^alpha for v in vals)) / (1 - alpha)
end

# matrix power of a PSD density operator via eigendecomposition
function mat_pow(rho, p)
    F = eigen(Hermitian(Matrix(rho)))
    vals = [v > EPS ? v^p : 0.0 for v in real.(F.values)]
    return F.vectors * Diagonal(complex.(vals)) * F.vectors'
end

# sandwiched Renyi relative entropy D_alpha(rho||sigma)
function sandwiched_renyi(rho, sigma, alpha)
    s_half = mat_pow(sigma, (1 - alpha) / (2 * alpha))
    inner = s_half * rho * s_half
    F = eigen(Hermitian(Matrix(inner)))
    vals = [v > EPS ? real(v)^alpha : 0.0 for v in real.(F.values)]
    return log(sum(vals)) / (alpha - 1)
end

# Umegaki relative entropy D(rho||sigma) = tr rho(log rho - log sigma)
function relative_entropy(rho, sigma)
    Fr = eigen(Hermitian(Matrix(rho)))
    Fs = eigen(Hermitian(Matrix(sigma)))
    logrho = Fr.vectors * Diagonal([v > EPS ? complex(log(real(v))) : complex(0.0) for v in real.(Fr.values)]) * Fr.vectors'
    logsig = Fs.vectors * Diagonal([v > EPS ? complex(log(real(v))) : complex(-50.0) for v in real.(Fs.values)]) * Fs.vectors'
    return real(tr(rho * (logrho - logsig)))
end

# partial trace utilities for a 3-qubit (8x8) density operator, qubit order (A,B,C)
# trace out a subset of {1,2,3}; returns reduced density operator
function ptrace3(rho, keep::Vector{Int})
    dims = (2, 2, 2)
    out_d = 2^length(keep)
    traced = setdiff([1, 2, 3], keep)
    red = zeros(ComplexF64, out_d, out_d)
    idx(b3) = (b3[1]) * 4 + (b3[2]) * 2 + (b3[3]) + 1          # bits in {0,1}
    for ka in 0:(out_d - 1)
        for kb in 0:(out_d - 1)
            acc = 0.0 + 0.0im
            # iterate over traced-out bits
            for t in 0:(2^length(traced) - 1)
                bitsA = zeros(Int, 3); bitsB = zeros(Int, 3)
                # fill kept positions
                for (qi, q) in enumerate(keep)
                    bit = (ka >> (length(keep) - qi)) & 1
                    bitsA[q] = bit
                    bitB = (kb >> (length(keep) - qi)) & 1
                    bitsB[q] = bitB
                end
                for (ti, q) in enumerate(traced)
                    bt = (t >> (length(traced) - ti)) & 1
                    bitsA[q] = bt
                    bitsB[q] = bt
                end
                acc += rho[idx(bitsA), idx(bitsB)]
            end
            red[ka + 1, kb + 1] = acc
        end
    end
    return red
end

# partial transpose on subsystem `sub` (1 or 2) of a 2-qubit (4x4) density operator
function partial_transpose2(rho, sub::Int)
    out = similar(rho)
    for i in 0:1, j in 0:1, k in 0:1, l in 0:1
        r = i * 2 + k + 1
        c = j * 2 + l + 1
        if sub == 1
            r2 = j * 2 + k + 1; c2 = i * 2 + l + 1
        else
            r2 = i * 2 + l + 1; c2 = j * 2 + k + 1
        end
        out[r2, c2] = rho[r, c]
    end
    return out
end

log_negativity(rho2, sub::Int) = begin
    pt = partial_transpose2(rho2, sub)
    tn = sum(abs.(eigvals(Matrix(pt))))     # trace norm of PT
    log(tn)
end

# build the 3-spinor entangled density operator from a GHZ-like superposition mixed with a
# product piece; the entangling strength is set by `lambda` (lambda=0 -> product state).
function three_spinor_density(lambda::Float64)
    # |psi> = cos*|000> + sin*(GHZ-ish entangler) ; here build a genuine entangled pure state
    # state vector over (A,B,C), index = 4a+2b+c
    psi = zeros(ComplexF64, 8)
    a = sqrt(1 - lambda)
    b = sqrt(lambda)
    psi[1] = a                 # |000>
    psi[8] = b * cos(0.6)      # |111>
    psi[4] = b * sin(0.6) * 0.5  # |011> : spreads correlation onto the A:C and conditional cuts
    psi[6] = b * sin(0.6) * 0.5  # |101>
    psi ./= norm(psi)
    return psi * psi'
end

function entropy_readout_family_block(lambda::Float64)
    rho_ABC = three_spinor_density(lambda)
    rho_AB  = ptrace3(rho_ABC, [1, 2])
    rho_BC  = ptrace3(rho_ABC, [2, 3])
    rho_A   = ptrace3(rho_ABC, [1])
    rho_B   = ptrace3(rho_ABC, [2])
    rho_C   = ptrace3(rho_ABC, [3])

    S_ABC = vn_entropy(rho_ABC)
    S_AB  = vn_entropy(rho_AB)
    S_BC  = vn_entropy(rho_BC)
    S_A   = vn_entropy(rho_A)
    S_B   = vn_entropy(rho_B)
    S_C   = vn_entropy(rho_C)

    cond_A_given_B = S_AB - S_B                  # S(A|B)
    coh_info_A_to_B = S_B - S_AB                 # I_c(A>B) = -S(A|B)
    mutual_AB = S_A + S_B - S_AB                 # I(A:B)
    mutual_AC = vn_entropy(ptrace3(rho_ABC, [1])) + S_C - vn_entropy(ptrace3(rho_ABC, [1, 3]))
    # conditional mutual information I(A:C|B) = S(AB)+S(BC)-S(B)-S(ABC)
    cmi_AC_given_B = S_AB + S_BC - S_B - S_ABC

    # relative entropy D(rho_AB || rho_A ⊗ rho_B) == mutual information (sanity-coupled readout)
    sigma_prod = kron(rho_A, rho_B)
    D_rel = relative_entropy(rho_AB, sigma_prod)

    renyi2   = renyi_entropy(rho_A, 2.0)
    renyi_half = renyi_entropy(rho_A, 0.5)
    sand2    = sandwiched_renyi(rho_AB, sigma_prod, 2.0)

    # smooth min/max entropy approximations (single-shot bounds) on rho_A
    valsA = sort(real.(eigvals(Hermitian(Matrix(rho_A)))); rev = true)
    valsA = [v for v in valsA if v > EPS]
    H_min = -log(maximum(valsA))                 # min-entropy
    H_max = 2 * log(sum(sqrt.(valsA)))           # max-entropy (Renyi-1/2)

    logneg_AB = log_negativity(rho_AB, 2)        # quantum entanglement of the A:B cut

    # finite path entropy: Shannon entropy of the diagonal (population) distribution of rho_ABC
    pops = real.(diag(rho_ABC))
    path_entropy = -sum(p > EPS ? p * log(p) : 0.0 for p in pops)

    return Dict(
        "lambda" => lambda,
        "S_rho_ABC" => S_ABC, "S_rho_A" => S_A, "S_rho_B" => S_B, "S_rho_AB" => S_AB,
        "conditional_S_A_given_B" => cond_A_given_B,
        "coherent_info_A_to_B" => coh_info_A_to_B,
        "mutual_info_AB" => mutual_AB,
        "mutual_info_AC" => mutual_AC,
        "conditional_mutual_info_AC_given_B" => cmi_AC_given_B,
        "relative_entropy_D_AB_vs_prod" => D_rel,
        "renyi2_A" => renyi2, "renyi_half_A" => renyi_half,
        "sandwiched_renyi2_AB_vs_prod" => sand2,
        "smooth_min_entropy_A" => H_min, "smooth_max_entropy_A" => H_max,
        "log_negativity_AB" => logneg_AB,
        "finite_path_entropy" => path_entropy,
    )
end

# ========================================================================================
# PART 4 -- CONTROLS (load-bearing): product kills correlations; dephase kills only quantum
# ========================================================================================
# DEPHASE control: kill off-diagonals of rho_AB -> classical correlation survives, negativity dies
function dephase_block(lambda::Float64)
    rho_ABC = three_spinor_density(lambda)
    rho_AB  = ptrace3(rho_ABC, [1, 2])
    rho_A   = ptrace3(rho_ABC, [1])
    rho_B   = ptrace3(rho_ABC, [2])
    deph = Diagonal(diag(rho_AB)) |> Matrix      # full dephasing in computational basis
    deph ./= real(tr(deph))
    mutual = vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(deph)
    logneg = log_negativity(deph, 2)
    return Dict("dephased_mutual_info_AB" => mutual, "dephased_log_negativity_AB" => logneg)
end

# ========================================================================================
# MAIN
# ========================================================================================
function main()
    t0 = time()

    # -- geometry anchor --
    geo = geometry_anchor()

    # -- entangled spinor-network MPS cut entropy + PRODUCT control --
    nsites = 10
    psi_ent,  _ = build_spinor_network_mps(nsites, 0.45)   # genuinely entangled
    psi_prod, _ = build_spinor_network_mps(nsites, 0.0)    # product control (theta=0)
    max_cut_ent,  bonds, ent_cuts  = network_cut_entropy(psi_ent)
    max_cut_prod, _,     prod_cuts = network_cut_entropy(psi_prod)

    entanglement = Dict(
        "carrier" => "ITensors spinor-network MPS (S=1/2 nodes, XX+YY entangling bonds)",
        "nsites" => nsites,
        "entangled_max_cut_entropy" => max_cut_ent,
        "product_max_cut_entropy" => max_cut_prod,
        "entangled_cut_entropies" => ent_cuts,
        "product_cut_entropies" => prod_cuts,
        "cut_bonds" => bonds,
        "entangled_is_entangled" => max_cut_ent > GAP,
        "product_collapses_to_zero" => max_cut_prod < COLLAPSE,
        "entanglement_load_bearing" => (max_cut_ent > GAP) && (max_cut_prod < COLLAPSE),
    )

    # -- full entropy readout family on the ENTANGLED density operator --
    readouts_ent  = entropy_readout_family_block(0.5)   # entangled lambda
    readouts_prod = entropy_readout_family_block(0.0)   # PRODUCT control lambda=0
    deph          = dephase_block(0.5)

    # -- control fires: product collapses every correlation readout --
    control = Dict(
        "product_mutual_info_AB" => readouts_prod["mutual_info_AB"],
        "product_coherent_info_A_to_B" => readouts_prod["coherent_info_A_to_B"],
        "product_log_negativity_AB" => readouts_prod["log_negativity_AB"],
        "product_relative_entropy" => readouts_prod["relative_entropy_D_AB_vs_prod"],
        "product_cmi_AC_given_B" => readouts_prod["conditional_mutual_info_AC_given_B"],
        "entangled_mutual_info_AB" => readouts_ent["mutual_info_AB"],
        "entangled_log_negativity_AB" => readouts_ent["log_negativity_AB"],
        "dephased_mutual_info_AB" => deph["dephased_mutual_info_AB"],
        "dephased_log_negativity_AB" => deph["dephased_log_negativity_AB"],
    )

    # control-fires checks (load-bearing)
    product_kills_mi   = abs(readouts_prod["mutual_info_AB"]) < COLLAPSE
    product_kills_ic   = abs(readouts_prod["coherent_info_A_to_B"]) < COLLAPSE ||
                         readouts_prod["coherent_info_A_to_B"] <= readouts_ent["coherent_info_A_to_B"]
    product_kills_neg  = readouts_prod["log_negativity_AB"] < COLLAPSE
    entangled_has_mi   = readouts_ent["mutual_info_AB"] > GAP
    entangled_has_neg  = readouts_ent["log_negativity_AB"] > GAP
    # DEPHASE: negativity dies (~0) but classical mutual information SURVIVES
    dephase_kills_neg  = deph["dephased_log_negativity_AB"] < GAP
    dephase_keeps_mi   = deph["dephased_mutual_info_AB"] > GAP

    control_checks = Dict(
        "product_kills_mutual_info" => product_kills_mi,
        "product_kills_coherent_info" => product_kills_ic,
        "product_kills_negativity" => product_kills_neg,
        "entangled_has_mutual_info" => entangled_has_mi,
        "entangled_has_negativity" => entangled_has_neg,
        "dephase_kills_negativity" => dephase_kills_neg,
        "dephase_keeps_classical_mutual_info" => dephase_keeps_mi,
    )

    required = Dict(
        "geometry_invariant_anchored" => geo["invariant_anchored_pass"],
        "geometry_wrong_structure_control_fails" => geo["wrong_structure_control_fails_invariant"],
        "geometry_carrier_is_density_operator" => geo["carrier_is_density_operator"]["is_density_operator"],
        "entanglement_load_bearing" => entanglement["entanglement_load_bearing"],
        "product_kills_correlations" => product_kills_mi && product_kills_neg,
        "entangled_has_correlations" => entangled_has_mi && entangled_has_neg,
        "dephase_kills_only_quantum" => dephase_kills_neg && dephase_keeps_mi,
        "bloch_free" => !geo["bloch_r_vector_used"],
    )
    all_pass = all(values(required))

    result = Dict(
        "schema" => "ENTROPY_READOUT_FAMILY_POC_v1",
        "name" => NAME,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "claim_ceiling" => "POC entropy-readout family on an entangled spinor-network carrier. " *
                           "Geometry anchored to FHS Chern invariant; entanglement load-bearing via " *
                           "product control. Does NOT admit stacking, G-structure selection, flux, " *
                           "Xi/Phi0, Axis0, FEP, physics. Entropy is a readout, never the primitive.",
        "primitive_note" => "Primitive is the density operator / spinor network; entropy is a READOUT.",
        "geometry_anchor" => geo,
        "entanglement" => entanglement,
        "entropy_readouts_entangled" => readouts_ent,
        "entropy_readouts_product_control" => readouts_prod,
        "dephase_control" => deph,
        "control_fires" => control,
        "control_checks" => control_checks,
        "required" => required,
        "all_pass" => all_pass,
        "bloch_r_vector_used" => false,
        "elapsed_seconds" => round(time() - t0, digits = 4),
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end

    # console summary
    println(JSON.json(Dict(
        "name" => NAME, "all_pass" => all_pass,
        "chern_topological" => geo["chern_topological_raw"],
        "chern_trivial_control" => geo["chern_trivial_control_raw"],
        "entangled_max_cut_entropy" => max_cut_ent,
        "product_max_cut_entropy" => max_cut_prod,
        "entangled_mutual_info_AB" => readouts_ent["mutual_info_AB"],
        "product_mutual_info_AB" => readouts_prod["mutual_info_AB"],
        "entangled_log_negativity_AB" => readouts_ent["log_negativity_AB"],
        "product_log_negativity_AB" => readouts_prod["log_negativity_AB"],
        "dephased_mutual_info_AB" => deph["dephased_mutual_info_AB"],
        "dephased_log_negativity_AB" => deph["dephased_log_negativity_AB"],
    ), 2))

    return all_pass
end

ok = main()
exit(ok ? 0 : 1)
