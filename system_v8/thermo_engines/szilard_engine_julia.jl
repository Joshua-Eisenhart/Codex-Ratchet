# Authoritative Julia leg for szilard_engine — QuantumOptics.jl projectors + entropies.
#
# Quantum-information form of the Szilard measurement/erasure cycle: a which-side
# register S (maximally mixed — the unmeasured 50/50 prior) and a 1-bit memory M
# (reset state). The projective which-side measurement, recorded into M via the
# projectors, licenses W/kT = I(S:M) = ln 2 of extraction per cycle; Landauer
# erasure of the memory costs S(M) = ln 2 in the same kT units, so the closed
# engine+reset cycle nets <= 0. A no-measurement control leaves I(S:M) = 0 and
# licenses no extraction. Entropies in nats ARE the kT-unit bookkeeping scalars.
using QuantumOptics
using JSON

b = SpinBasis(1//2)
sideL = spinup(b); sideR = spindown(b)     # which half the molecule occupies
mem0 = spinup(b);  mem1 = spindown(b)      # 1-bit memory: reset / flipped

P_L = projector(sideL); P_R = projector(sideR)
M0 = projector(mem0);   M1 = projector(mem1)
rho_S = 0.5 * (P_L + P_R)                  # unknown side: maximally mixed

# Measurement: the which-side outcome is recorded into the memory via projectors.
joint = tensor(P_L * rho_S * P_L, M0) + tensor(P_R * rho_S * P_R, M1)
joint_blind = tensor(rho_S, M0)            # control: no measurement, memory untouched

S_S_prior = real(entropy_vn(rho_S))        # ln 2: the one-bit 50/50 prior (nats)
S_joint   = real(entropy_vn(joint))
rho_M     = ptrace(joint, 1)               # trace out S -> memory marginal
rho_Spost = ptrace(joint, 2)               # trace out M -> side marginal
S_M       = real(entropy_vn(rho_M))
S_Spost   = real(entropy_vn(rho_Spost))

extracted_work_kT = S_Spost + S_M - S_joint        # I(S:M) = ln 2, extraction licensed
erasure_cost_kT   = S_M                            # Landauer: memory reset >= kT ln 2
net_work_kT       = extracted_work_kT - erasure_cost_kT   # closed cycle: 0
info_acquired_bits = (S_S_prior - (S_joint - S_M)) / log(2.0)   # S(S)-S(S|M) = 1 bit

S_joint_blind = real(entropy_vn(joint_blind))
blind_extracted_work_kT = real(entropy_vn(ptrace(joint_blind, 2))) +
                          real(entropy_vn(ptrace(joint_blind, 1))) - S_joint_blind

out = Dict(
    "engine" => "julia:QuantumOptics",
    "extracted_work_kT" => extracted_work_kT,
    "erasure_cost_kT" => erasure_cost_kT,
    "net_work_kT" => net_work_kT,
    "info_acquired_bits" => info_acquired_bits,
    "blind_extracted_work_kT" => blind_extracted_work_kT,
    "landauer_saturated" => abs(extracted_work_kT - log(2.0)) < 1e-9,
    "second_law_net_nonpositive" => (net_work_kT <= 1e-12),
)
println(JSON.json(out))
