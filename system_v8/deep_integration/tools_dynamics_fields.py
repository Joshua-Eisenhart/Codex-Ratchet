#!/usr/bin/env python3
"""Deep-integration lane: dynamics_fields (pysindy DEEP + galois DEEP).

UNOFFICIAL / working-sim bar. NOT proof-level. promotion_allowed: false.

Part 1 — pysindy DEEP (model identification, load-bearing):
  * Load the julia_manifold engine-native receipt's 30-tick base series
    (S_L, S_LR, I, flux, dC-as-record).
  * Regenerate a finer 200-step tick series with a small LOCAL GKSL loop:
    single-qubit amplitude damping (L = sqrt(gamma) sigma_-, H = 0),
    RK4-integrated master equation. The Bloch-z component obeys the known
    analytic law  r_z' = gamma * (1 - r_z).
  * Fit SINDy (polynomial library) to the r_z trajectory. The recovered
    constant and linear coefficients must match +gamma and -gamma to 5%,
    and higher-order terms must be negligible (linear form). SINDy's
    regression DECIDES these checks — pysindy is load-bearing.
  * Fit the drive-coupled quotient-entropy series (S_LR, 30 ticks) both
    alone and jointly with (flux, I); report discovered structure honestly.

Part 2 — galois DEEP (field arithmetic, load-bearing):
  * Rebuild the T5 out-of-grammar F_7 packet (quadratic residues {1,2,4})
    using galois GF(7) arithmetic (field mul + is_square + legendre).
    The accepted-word set must byte-match the archived t5_gf7 packet.
  * Extend to GF(8) = GF(2^3) — a REAL field the int-mod approach cannot
    build (Z/8 has zero divisors: 2*4 = 0 mod 8). Build a genuinely new
    multiplication packet from field trace + discrete log projections and
    run the base MSS admissibility engine over it (alone and welded).

Run with /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3.
Heavy stacks (torch/jax/julia) are NOT loaded — light-lib lane only.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = ROOT / "system_v8" / "deep_integration"
OUTDIR = HERE / "results" / "dynamics_fields"

JULIA_RECEIPT = ROOT / "system_v8" / "engine_native" / "results" / "julia_manifold" / "receipt.json"
SOURCE_PACKETS = ROOT / "system_v8" / "manifold" / "results" / "source_packets.json"
BASE_MSS = ROOT / "system_v8" / "manifold" / "results" / "base_mss.json"
T5_RESULT = ROOT / "system_v8" / "manifold" / "results" / "t5_out_of_grammar.json"
MANIFOLD_ENGINE = ROOT / "system_v8" / "manifold" / "engine"


# ------------------------------------------------------------------ helpers
def refuse_to_reuse(outdir: Path) -> None:
    if outdir.exists():
        raise SystemExit(f"REFUSE-TO-REUSE: output dir already exists: {outdir}")
    outdir.mkdir(parents=True, exist_ok=False)


# ------------------------------------------------- Part 1a: local GKSL loop
def gksl_bloch_series(gamma: float, n_steps: int, dt: float):
    """Single-qubit amplitude damping GKSL, RK4 on the 2x2 density matrix.

    L = sqrt(gamma) sigma_- = sqrt(gamma) |0><1|, H = 0.
    Known analytic law: r_z' = gamma (1 - r_z), r_z = Tr(rho sigma_z).
    """
    sm = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)  # |0><1|
    sp_ = sm.conj().T
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    n_op = sp_ @ sm

    def drho(rho):
        return gamma * (sm @ rho @ sp_ - 0.5 * (n_op @ rho + rho @ n_op))

    rho = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)  # excited |1><1|, r_z0 = -1
    rz = np.empty(n_steps + 1)
    ts = np.empty(n_steps + 1)
    for k in range(n_steps + 1):
        rz[k] = np.real(np.trace(rho @ sz))
        ts[k] = k * dt
        k1 = drho(rho)
        k2 = drho(rho + 0.5 * dt * k1)
        k3 = drho(rho + 0.5 * dt * k2)
        k4 = drho(rho + dt * k3)
        rho = rho + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        rho = 0.5 * (rho + rho.conj().T)
        rho = rho / np.real(np.trace(rho))
    return ts, rz


def part1_pysindy(receipt: dict) -> tuple[dict, dict, list[str]]:
    import pysindy as ps

    findings: list[str] = []
    bs = receipt["data"]["base_series"]
    series = {k: np.asarray(bs[k], dtype=float)
              for k in ("S_L", "S_LR", "I", "flux", "dC")}
    assert all(len(v) == 30 for v in series.values())

    gamma_series = np.asarray(bs["gamma"], dtype=float)
    gamma = float(np.mean(gamma_series))  # receipt-derived rate for the local loop
    findings.append(
        f"local GKSL gamma = mean(julia_manifold gamma series) = {gamma:.6f} "
        f"(series cycles over {sorted(set(np.round(gamma_series, 6)))})")

    # finer 200-step tick series
    n_steps, dt = 200, 8.0 / 200
    ts, rz = gksl_bloch_series(gamma, n_steps, dt)
    # integrator sanity vs analytic solution r_z(t) = 1 - 2 exp(-gamma t)
    analytic = 1.0 - 2.0 * np.exp(-gamma * ts)
    integ_err = float(np.max(np.abs(rz - analytic)))

    # ---- SINDy identification of the damped Bloch law (LOAD-BEARING) ----
    model = ps.SINDy(
        optimizer=ps.STLSQ(threshold=0.01),
        feature_library=ps.PolynomialLibrary(degree=3),
    )
    model.fit(rz.reshape(-1, 1), t=dt)
    names = model.get_feature_names()
    coefs = model.coefficients()[0]
    cmap = dict(zip(names, coefs))
    c_const = float(cmap.get("1", 0.0))
    c_lin = float(cmap.get("x0", 0.0))
    c_quad = float(cmap.get("x0^2", 0.0))
    c_cub = float(cmap.get("x0^3", 0.0))
    score = float(model.score(rz.reshape(-1, 1), t=dt))

    rel_const = abs(c_const - gamma) / gamma
    rel_lin = abs(c_lin - (-gamma)) / gamma
    nonlinear_frac = max(abs(c_quad), abs(c_cub)) / gamma

    checks = {
        "gksl_integrator_matches_analytic_lt_1e-6": integ_err < 1e-6,
        "sindy_bloch_const_coeff_matches_gamma_5pct": rel_const <= 0.05,
        "sindy_bloch_linear_coeff_matches_minus_gamma_5pct": rel_lin <= 0.05,
        "sindy_bloch_form_is_linear_no_higher_terms": nonlinear_frac <= 0.05,
        "sindy_bloch_model_score_above_0.999": score > 0.999,
    }
    findings.append(
        f"SINDy recovered (r_z)' = {c_const:.6f} + {c_lin:.6f} r_z "
        f"(quad {c_quad:.2e}, cubic {c_cub:.2e}); target gamma(1-r_z) with "
        f"gamma={gamma:.6f}; rel errors const {rel_const:.3%}, lin {rel_lin:.3%}; "
        f"R^2={score:.6f}. pysindy regression decides these checks (load-bearing).")

    # ---- drive-coupled quotient-entropy series: honest discovery ----
    t30 = np.arange(30, dtype=float)
    slr = series["S_LR"].reshape(-1, 1)
    m_alone = ps.SINDy(optimizer=ps.STLSQ(threshold=0.02),
                       feature_library=ps.PolynomialLibrary(degree=2))
    m_alone.fit(slr, t=t30)
    score_alone = float(m_alone.score(slr, t=t30))
    eq_alone = m_alone.equations(precision=4)[0]

    X = np.column_stack([series["S_LR"], series["flux"], series["I"]])
    m_joint = ps.SINDy(optimizer=ps.STLSQ(threshold=0.02),
                       feature_library=ps.PolynomialLibrary(degree=2))
    m_joint.fit(X, t=t30)
    score_joint = float(m_joint.score(X, t=t30))
    eq_joint = m_joint.equations(precision=4)[0]

    checks["sindy_quotient_entropy_fits_finite"] = bool(
        np.all(np.isfinite(m_alone.coefficients()))
        and np.all(np.isfinite(m_joint.coefficients()))
        and np.isfinite(score_alone) and np.isfinite(score_joint))
    findings.append(
        f"quotient-entropy S_LR autonomous 1-var fit: (S_LR)' = {eq_alone}; "
        f"R^2={score_alone:.4f}. Joint (S_LR,flux,I) fit: (S_LR)' = {eq_joint}; "
        f"R^2(all states)={score_joint:.4f}. HONEST record: the 30-tick "
        f"drive-coupled series rises then falls under a period-3 gamma "
        f"schedule, so no autonomous low-order polynomial ODE in S_LR alone "
        f"can represent it; the discovered structure is weak/trivial and is "
        f"recorded as such, not promoted.")

    data = {
        "gamma_used": gamma,
        "gksl_steps": n_steps,
        "gksl_dt": dt,
        "gksl_integrator_max_err_vs_analytic": integ_err,
        "sindy_bloch": {
            "feature_names": names,
            "coefficients": [float(c) for c in coefs],
            "const_coeff": c_const, "linear_coeff": c_lin,
            "quad_coeff": c_quad, "cubic_coeff": c_cub,
            "rel_err_const": rel_const, "rel_err_linear": rel_lin,
            "score": score,
        },
        "sindy_quotient_entropy": {
            "alone_equation": eq_alone, "alone_score": score_alone,
            "joint_equation": eq_joint, "joint_score": score_joint,
        },
        "receipt_series_lengths": {k: int(len(v)) for k, v in series.items()},
    }
    return checks, data, findings


# ---------------------------------------------------- Part 2: galois DEEP
def part2_galois() -> tuple[dict, dict, list[str]]:
    import galois

    sys.path.insert(0, str(MANIFOLD_ENGINE))
    import source_packets as sp  # noqa: E402
    from base_mss_engine import run as run_base  # noqa: E402

    findings: list[str] = []
    checks: dict[str, bool] = {}

    # ---- GF(7): rebuild the T5 packet with real field arithmetic ----
    GF7 = galois.GF(7)
    qr_squares = {int(GF7(x) ** 2) for x in range(1, 7)}
    qr_legendre = {x for x in range(1, 7) if galois.legendre_symbol(x, 7) == 1}
    qr_is_square = {x for x in range(1, 7) if bool(GF7(x).is_square())}
    checks["galois_gf7_qr_set_is_124_all_three_methods"] = (
        qr_squares == {1, 2, 4} == qr_legendre == qr_is_square)

    words = set()
    for a, b in itertools.product(range(1, 7), repeat=2):
        fa, fb = GF7(a), GF7(b)
        p = fa * fb                      # field multiplication (galois)
        bits = (int(bool(fa.is_square())), int(bool(fb.is_square())),
                int(bool(p.is_square())), int(p) % 2)
        words.add(bits)
    gf7_packet = sp.packet(
        "gf7_multiplication_galois_rebuild",
        "system_v8/deep_integration/tools_dynamics_fields.py::part2_galois GF(7) via galois",
        ["a_is_QR", "b_is_QR", "product_is_QR", "product_parity"],
        words, "source_observation")

    t5 = json.loads(T5_RESULT.read_text())
    t5_gf7 = next(p for p in t5["t5_packets"]
                  if p["packet_id"] == "t5_gf7_multiplication")
    checks["galois_gf7_packet_words_match_t5_archive"] = (
        gf7_packet["accepted_words"] == t5_gf7["accepted_words"])
    findings.append(
        f"GF(7) rebuild via galois: QR set {sorted(qr_squares)} from squares, "
        f"legendre_symbol, and is_square all agree; packet words "
        f"{gf7_packet['accepted_words']} vs T5 archive "
        f"{t5_gf7['accepted_words']} — galois arithmetic decides the match "
        f"(load-bearing).")

    # ---- GF(8) = GF(2^3): a REAL field int-mod cannot build ----
    GF8 = galois.GF(2 ** 3)
    intmod8_zero_divisors = sorted(
        (a, b) for a, b in itertools.product(range(1, 8), repeat=2)
        if (a * b) % 8 == 0)
    gf8_unit_products_nonzero = all(
        int(GF8(a) * GF8(b)) != 0
        for a, b in itertools.product(range(1, 8), repeat=2))
    checks["galois_gf8_units_closed_intmod8_has_zero_divisors"] = (
        gf8_unit_products_nonzero and len(intmod8_zero_divisors) > 0)
    # char-2 field-theoretic distinction: Frobenius bijective -> all squares
    checks["galois_gf8_every_element_square_unlike_gf7"] = (
        all(bool(GF8(x).is_square()) for x in range(1, 8))
        and not all(bool(GF7(x).is_square()) for x in range(1, 7)))

    words8 = set()
    for a, b in itertools.product(range(1, 8), repeat=2):
        fa, fb = GF8(a), GF8(b)
        p = fa * fb                      # extension-field multiplication
        bits = (int(fa.field_trace()), int(fb.field_trace()),
                int(p.field_trace()), int(np.log(p)) % 2)
        words8.add(bits)
    gf8_packet = sp.packet(
        "gf8_ext_field_multiplication",
        "system_v8/deep_integration/tools_dynamics_fields.py::part2_galois "
        f"GF(2^3) irreducible {GF8.irreducible_poly}, trace+dlog projection",
        ["a_trace", "b_trace", "product_trace", "product_dlog_parity"],
        words8, "source_observation")
    checks["galois_gf8_packet_width_four_nonempty"] = (
        gf8_packet["width"] == 4 and gf8_packet["accepted_count"] > 0)

    # ---- base MSS admissibility engine over the new packet ----
    source = json.loads(SOURCE_PACKETS.read_text())
    prev = json.loads(BASE_MSS.read_text())
    prev_frontier = sorted(prev["heldout_frontier"])

    def with_packets(pkts):
        s = dict(source)
        s["base_packets"] = pkts
        return run_base(s)

    gf8_alone = with_packets([gf8_packet])
    gf8_welded = with_packets(source["base_packets"] + [gf8_packet])

    checks["gf8_alone_base_engine_process_checks_pass"] = bool(gf8_alone["all_pass"])
    checks["gf8_welded_base_engine_process_checks_pass"] = bool(gf8_welded["all_pass"])
    checks["gf8_welded_simulated_ten_packets"] = gf8_welded["packet_count"] == 10
    frontier_changed = sorted(gf8_welded["heldout_frontier"]) != prev_frontier
    findings.append(
        f"GF(8) packet ({gf8_packet['accepted_count']} words "
        f"{gf8_packet['accepted_words']}) run through base MSS engine: alone "
        f"frontier {gf8_alone['heldout_frontier']}, welded (9+1) frontier "
        f"{gf8_welded['heldout_frontier']}, previous frontier {prev_frontier}, "
        f"frontier_changed_by_gf8={frontier_changed}. Z/8 zero-divisor pairs "
        f"{intmod8_zero_divisors} witness that int-mod cannot build this "
        f"field; only galois extension-field arithmetic (poly "
        f"{GF8.irreducible_poly}, trace, dlog) produced this packet "
        f"(load-bearing).")

    data = {
        "gf7_qr_squares": sorted(qr_squares),
        "gf7_qr_legendre": sorted(qr_legendre),
        "gf7_packet": gf7_packet,
        "t5_gf7_archive_digest": t5_gf7["packet_digest"],
        "gf8_irreducible_poly": str(GF8.irreducible_poly),
        "intmod8_zero_divisor_pairs": intmod8_zero_divisors,
        "gf8_packet": gf8_packet,
        "gf8_alone_frontier": gf8_alone["heldout_frontier"],
        "gf8_alone_purgatory": gf8_alone["purgatory"],
        "gf8_welded_frontier": gf8_welded["heldout_frontier"],
        "previous_heldout_frontier": prev_frontier,
        "frontier_changed_by_gf8": frontier_changed,
    }
    return checks, data, findings


# ------------------------------------------------------------------- main
def main() -> int:
    refuse_to_reuse(OUTDIR)
    receipt_in = json.loads(JULIA_RECEIPT.read_text())

    checks1, data1, f1 = part1_pysindy(receipt_in)
    checks2, data2, f2 = part2_galois()

    checks = {**checks1, **checks2}
    findings = f1 + f2
    all_pass = all(checks.values())

    receipt = {
        "schema": "ratchet.v8.deep-integration.dynamics-fields.v0",
        "lane": "dynamics_fields",
        "bar": "UNOFFICIAL working-sim; NOT proof-level",
        "inputs": {
            "julia_manifold_receipt": str(JULIA_RECEIPT),
            "source_packets": str(SOURCE_PACKETS),
            "base_mss": str(BASE_MSS),
            "t5_out_of_grammar": str(T5_RESULT),
        },
        "packages": {
            "pysindy": ("load_bearing: SINDy regression coefficients decide the "
                        "Bloch-law identification checks (const=+gamma, "
                        "linear=-gamma, linear form)"),
            "galois": ("load_bearing: GF(7) field mul/is_square/legendre decide "
                       "the T5 word match; GF(2^3) extension arithmetic is the "
                       "only constructor of the gf8 packet"),
            "numpy": "supportive: RK4 GKSL integrator + series handling",
        },
        "checks": checks,
        "all_pass": all_pass,
        "data": {"part1_pysindy": data1, "part2_galois": data2},
        "findings": findings,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("working-sim diagnostics: package-level deep integration "
                          "evidence only; no canonical, bridge, or admission claim"),
    }
    out = OUTDIR / "receipt.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"lane": "dynamics_fields", "file": str(out),
                      "all_pass": all_pass, "checks": checks}, sort_keys=True))
    for line in findings:
        print("FINDING:", line)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
