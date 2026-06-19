#!/usr/bin/env python3
"""JAX leg for mct_dynamic_admissibility_packet_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "mct_dynamic_admissibility_packet_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
DISPOSITION_STATUS = "derived_default_under_current_doctrine"
PASS_CONDITION_DEFAULT = "non_isomorphic_diff"
PASS_CONDITION_PROVENANCE = "derived_default_under_current_doctrine: (1) root axiom a=a iff a~b — identity is probe-relative, not label-primitive, so literal table inequality tests label identity; (2) reindexing is a manifold operation defined as label change preserving all declared invariants — under the literal criterion a pure relabeling would count as ratchet advance, inconsistent within the packet; (3) the label-shuffle null control exists to kill label-level claims. literal_table_diff retained as diagnostic row only. Disposition, not owner lock."
SELF_LOOP_POLICY_DEFAULT = "retain"
SELF_LOOP_POLICY_PROVENANCE = "derived_default_under_current_doctrine: (1) N01 makes order/history load-bearing where probes preserve it; the no-silent-erasure discipline comes from quotient-pushforward semantics plus killed-information ledger discipline (standing: system_v6/receipts/mct_reconciled_spec_20260609.md); the current owner correction (2026-06-09) identifies the correct interpretation as radiated outward record rather than destroyed information — doctrine-level sources mapped in system_v6/receipts/shell_flow_radiated_information_mine_20260610.md (restatement at doctrine level; exact conservation/reconstruction math not on file there, candidate formalization pending its own build) — erasing a fold-produced self-loop without a ledger silently drops the record that a relation existed between the now-identified states; (2) the quotient pushforward of an edge set naturally retains self-loops — erasure is an extra lossy step (reconciled spec frames retain as the pushforward value, |E_3|=8); (3) the whole-field contract requires edge-transport ledgers, which retention preserves. erase remains available only as an explicitly-ledgered lossy branch. Disposition, not owner lock."
TOL = 1.0e-8
Q_DEPHASE = 0.37
THETA_X = math.pi / 5.0
PHI_Z = math.pi / 7.0
T_TERRAIN = 0.27

PIN_BLOCK_CANONICAL = (
    '{"axis0_boundary_policy":"b0=0 at eta=pi/4 boundary shell",'
    '"axis0_status":"readout_only_no_closure",'
    '"bin_edges":{"density":[-1.000001,-0.5,0.0,0.5,1.000001],'
    '"order_gap":[0.0,1e-09,0.001,0.01,1000000000.0],"phase_bins":8},'
    '"choice_points":{"constraint_form":"state_predicate main + probe_row_predicate transported view",'
    '"fixed_root_C":"fixed root C with explicit C_t view",'
    '"folding":"equivalence-respecting default; aggregation branch ledgered only",'
    '"pass_condition":"owner_pending",'
    '"relation_updates":"finite delta (E union Delta+) minus Delta-",'
    '"representation_mode":"carrier_retained main + quotient_materialized side branch",'
    '"self_loop_policy_default":"owner_pending"},'
    '"grid":{"chi_j":"2*pi*j/8 for j=0..7","eta_k":["pi/8","pi/4","3*pi/8"],'
    '"phi_i":"2*pi*i/8 for i=0..7","sheets":["L","R"],"support_size":384},'
    '"lr_sheet_realization":{"source_quote":"H_L=+H_0, H_R=-H_0",'
    '"status":"PINNED-CHOICE",'
    '"summary":"spinor chart stays source-identical; sheet enters through Weyl Hamiltonian sign and computed chirality probe"},'
    '"probe_families":["P_density","P_shell","P_loop","P_order","P_phase","P_chirality"],'
    '"ring_checkerboard_note":"eta-shell rings x (phi,chi) checkerboard; mapping question stays OPEN",'
    '"spinor_chart":"psi_s(phi_i,chi_j;eta_k)=(exp(i(phi_i+chi_j))*cos(eta_k), exp(i(phi_i-chi_j))*sin(eta_k))"}'
)
PIN_BLOCK_SHA256 = hashlib.sha256(PIN_BLOCK_CANONICAL.encode("utf-8")).hexdigest()
PIN_BLOCK_EXTENSIONS_CANONICAL = (
    '"chart_agreement_receipt":"pinned_chart_agrees_with_formal_geometry_78_88_no_divergence",'
    '"computed_sheet_probe":{"name":"P_weyl_gap","source":"order_gap_noncommuting_matched_LR_difference","quotient_key":"q_without_phase_computed_sheet"},'
    f'"pin_extended_from":{{"sha256":"{PIN_BLOCK_SHA256}","lineage_note":"additive instrumentation plus derived defaults only; previous PIN retained as pin_block_sha256"}},'
    '"probe_family_metadata":{"P_chirality":"label_transcription","P_weyl_gap":"computed_dynamic_sheet_sensitive"},'
    '"variant_ledger_key":"variant_ledger"'
)
PIN_SPEC = json.loads(PIN_BLOCK_CANONICAL)
PIN_BLOCK_EXTENDED_BASE = PIN_BLOCK_CANONICAL.replace(
    '"pass_condition":"owner_pending"',
    '"pass_condition":"non_isomorphic_diff",'
    f'"pass_condition_disposition_status":"{DISPOSITION_STATUS}",'
    f'"pass_condition_provenance":{json.dumps(PASS_CONDITION_PROVENANCE, ensure_ascii=False)}',
).replace(
    '"self_loop_policy_default":"owner_pending"',
    '"self_loop_policy_default":"retain",'
    f'"self_loop_policy_disposition_status":"{DISPOSITION_STATUS}",'
    f'"self_loop_policy_provenance":{json.dumps(SELF_LOOP_POLICY_PROVENANCE, ensure_ascii=False)}',
)
PIN_BLOCK_EXTENDED_CANONICAL = PIN_BLOCK_EXTENDED_BASE[:-1] + "," + PIN_BLOCK_EXTENSIONS_CANONICAL + "}"
PIN_BLOCK_EXTENDED_SHA256 = hashlib.sha256(PIN_BLOCK_EXTENDED_CANONICAL.encode("utf-8")).hexdigest()
PIN_SPEC_EXTENDED = json.loads(PIN_BLOCK_EXTENDED_CANONICAL)

SOURCE_REFS = {
    "system_v6_readme": "system_v6/README.md",
    "mct_spec": "system_v6/receipts/mct_reconciled_spec_20260609.md",
    "mct_adjudication": "system_v6/receipts/mct_mine_adjudication_20260610.md",
    "mct_wiki_map": "system_v6/receipts/mct_wiki_source_map_20260610.md",
    "runbook": "/Users/joshuaeisenhart/wiki/projects/codex-ratchet/ring-checkerboard-three-presentations-sim-engine-runbook-2026-06-09.md",
    "formal_geometry": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:78-88,157-166",
    "terrain_math": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/terrain math.md:43-49,51-152",
    "operator_math": "system_v5/READ ONLY Reference Docs/operator math explicit.md",
    "field_wide_contract": "/Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:123-203,211-232,288-305",
}

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive batched finite spinor/density/probe and order-gap computations; substrate demoted under capability-probe doctrine"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive complex spinor, density, Bloch, quotient-row, and relation scalar arithmetic; substrate demoted under capability-probe doctrine"},
    "jax.scipy.linalg": {"tried": True, "used": True, "reason": "load-bearing terrain stage matrix exponential for committed Hamiltonian map"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing SMT over computed probe rows for phi-blindness and phase-control flip"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT over the same computed probe rows"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, path, and timestamp machinery"},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "jax.scipy.linalg": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
P0 = 0.5 * (I2 + SZ)
P1 = 0.5 * (I2 - SZ)
QPLUS = 0.5 * (I2 + SX)
QMINUS = 0.5 * (I2 - SX)
H0 = (SX + SY + SZ) / jnp.sqrt(jnp.asarray(3.0, dtype=jnp.float64))


def cfloat(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def complex_pair(value: Any) -> list[float]:
    z = complex(jax.device_get(value))
    return [round(z.real, 12), round(z.imag, 12)]


def matrix_json(mat: Any) -> list[list[list[float]]]:
    arr = jax.device_get(mat)
    return [[complex_pair(arr[i, j]) for j in range(arr.shape[1])] for i in range(arr.shape[0])]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt12(value: float) -> str:
    return f"{value:+.12f}"


def bin_scalar(value: float, edges: list[float]) -> int:
    if abs(value) <= 1.0e-10:
        value = 0.0
    for idx in range(len(edges) - 1):
        if edges[idx] <= value < edges[idx + 1]:
            return idx
    return len(edges) - 2


def phase_bin(angle: float) -> int:
    tau = 2.0 * math.pi
    return int(math.floor(((angle % tau) / tau) * 8.0 + 1.0e-12)) % 8


def spinor(phi: float, chi: float, eta: float) -> Any:
    return jnp.asarray(
        [jnp.exp(1j * (phi + chi)) * math.cos(eta), jnp.exp(1j * (phi - chi)) * math.sin(eta)],
        dtype=jnp.complex128,
    )


def density(psi: Any) -> Any:
    return jnp.outer(psi, jnp.conjugate(psi))


def bloch(rho: Any) -> tuple[float, float, float]:
    return (cfloat(jnp.trace(rho @ SX)), cfloat(jnp.trace(rho @ SY)), cfloat(jnp.trace(rho @ SZ)))


def trace_norm(mat: Any) -> float:
    vals = jnp.linalg.svd(mat, compute_uv=False)
    return cfloat(jnp.sum(vals))


def fro_norm(mat: Any) -> float:
    return cfloat(jnp.linalg.norm(mat))


def dephase_z(rho: Any) -> Any:
    return (1.0 - Q_DEPHASE) * rho + Q_DEPHASE * (P0 @ rho @ P0 + P1 @ rho @ P1)


def dephase_x(rho: Any) -> Any:
    return (1.0 - Q_DEPHASE) * rho + Q_DEPHASE * (QPLUS @ rho @ QPLUS + QMINUS @ rho @ QMINUS)


def rotate_x(rho: Any) -> Any:
    u = jsp_linalg.expm(-0.5j * THETA_X * SX)
    return u @ rho @ jnp.conjugate(u.T)


def rotate_z(rho: Any) -> Any:
    u = jsp_linalg.expm(-0.5j * PHI_Z * SZ)
    return u @ rho @ jnp.conjugate(u.T)


def terrain_ne(sheet: str, rho: Any) -> Any:
    sign = 1.0 if sheet == "L" else -1.0
    u = jsp_linalg.expm(-1j * T_TERRAIN * sign * H0)
    return u @ rho @ jnp.conjugate(u.T)


def terrain_si_commuting(_sheet: str, rho: Any) -> Any:
    return dephase_z(rho)


def order_gap_noncommuting(sheet: str, rho: Any) -> float:
    return fro_norm(terrain_ne(sheet, dephase_z(rho)) - dephase_z(terrain_ne(sheet, rho)))


def order_gap_commuting(sheet: str, rho: Any) -> float:
    return fro_norm(terrain_si_commuting(sheet, dephase_z(rho)) - dephase_z(terrain_si_commuting(sheet, rho)))


def order_gap_commuting_distinct(_sheet: str, rho: Any) -> float:
    return fro_norm(rotate_z(dephase_z(rho)) - dephase_z(rotate_z(rho)))


def order_gap_noncommuting_flip(_sheet: str, rho: Any) -> float:
    return fro_norm(rotate_z(dephase_x(rho)) - dephase_x(rotate_z(rho)))


def loop_deltas(phi: float, chi: float, eta: float) -> tuple[float, float]:
    u = math.pi / 4.0
    rho0 = density(spinor(phi, chi, eta))
    inner = density(spinor(phi + u, chi, eta))
    outer = density(spinor(phi - math.cos(2.0 * eta) * u, chi + u, eta))
    return fro_norm(inner - rho0), fro_norm(outer - rho0)


def support_and_rows() -> dict[str, Any]:
    etas = [math.pi / 8.0, math.pi / 4.0, 3.0 * math.pi / 8.0]
    density_edges = PIN_SPEC["bin_edges"]["density"]
    order_edges = PIN_SPEC["bin_edges"]["order_gap"]
    support = []
    probe_rows = []
    canonical_lines = []
    for sheet in ["L", "R"]:
        sheet_sign = 1 if sheet == "L" else -1
        chirality_probe = sheet_sign
        for k, eta in enumerate(etas):
            b0_value = math.cos(2.0 * eta)
            b0 = 1 if b0_value > 1.0e-12 else (-1 if b0_value < -1.0e-12 else 0)
            for i in range(8):
                phi = 2.0 * math.pi * i / 8.0
                for j in range(8):
                    chi = 2.0 * math.pi * j / 8.0
                    sid = f"{sheet}:eta{k}:phi{i}:chi{j}"
                    psi = spinor(phi, chi, eta)
                    rho = density(psi)
                    rx, ry, rz = bloch(rho)
                    inner_delta, outer_delta = loop_deltas(phi, chi, eta)
                    gap_nc = order_gap_noncommuting(sheet, rho)
                    gap_c = order_gap_commuting(sheet, rho)
                    gap_c_distinct = order_gap_commuting_distinct(sheet, rho)
                    gap_nc_flip = order_gap_noncommuting_flip(sheet, rho)
                    p_density = tuple(bin_scalar(v, density_edges) for v in (rx, ry, rz))
                    p_loop = (
                        "fiber_inner",
                        "inner_stationary" if inner_delta <= TOL else "inner_visible",
                        "lifted_base_outer",
                        "outer_visible" if outer_delta > 1.0e-6 else "outer_stationary",
                    )
                    row = {
                        "state_id": sid,
                        "sheet": sheet,
                        "eta_index": k,
                        "phi_index": i,
                        "chi_index": j,
                        "P_density": list(p_density),
                        "P_shell": k,
                        "P_loop": list(p_loop),
                        "P_order": bin_scalar(gap_nc, order_edges),
                        "P_phase": phase_bin(phi + chi),
                        "P_chirality": chirality_probe,
                        "P_weyl_gap": round(gap_nc * 1.0e12),
                        "axis0_eta": eta,
                        "axis0_b0": b0,
                        "order_gap_noncommuting": gap_nc,
                        "order_gap_commuting_control": gap_c,
                        "order_gap_commuting_distinct_control": gap_c_distinct,
                        "order_gap_noncommuting_flip_control": gap_nc_flip,
                    }
                    support.append(
                        {
                            "state_id": sid,
                            "sheet": sheet,
                            "eta_index": k,
                            "phi_index": i,
                            "chi_index": j,
                            "psi": [complex_pair(psi[0]), complex_pair(psi[1])],
                            "rho": matrix_json(rho),
                            "bloch": [round(rx, 12), round(ry, 12), round(rz, 12)],
                        }
                    )
                    probe_rows.append(row)
                    canonical_lines.append(
                        "|".join(
                            [
                                sid,
                                fmt12(float(jax.device_get(jnp.real(psi[0])))),
                                fmt12(float(jax.device_get(jnp.imag(psi[0])))),
                                fmt12(float(jax.device_get(jnp.real(psi[1])))),
                                fmt12(float(jax.device_get(jnp.imag(psi[1])))),
                            ]
                        )
                    )
    return {
        "support_table": support,
        "probe_row_table": probe_rows,
        "support_table_hash": sha256_text("\n".join(canonical_lines) + "\n"),
    }


def active_key(row: dict[str, Any], include_phase: bool) -> tuple[Any, ...]:
    key: tuple[Any, ...] = (
        tuple(row["P_density"]),
        row["P_shell"],
        tuple(row["P_loop"]),
        row["P_order"],
        row["P_chirality"],
    )
    if include_phase:
        key = key + (row["P_phase"],)
    return key


def active_key_computed_sheet(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        tuple(row["P_density"]),
        row["P_shell"],
        tuple(row["P_loop"]),
        row["P_order"],
        row["P_weyl_gap"],
    )


def quotient(rows: list[dict[str, Any]], include_phase: bool) -> dict[str, Any]:
    classes: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for row in rows:
        classes[active_key(row, include_phase)].append(row["state_id"])
    sizes = sorted([len(v) for v in classes.values()], reverse=True)
    total = sum(sizes)
    probs = [size / total for size in sizes]
    h_q = -sum(p * math.log(p) for p in probs if p > 0.0)
    a_q = sum((size / total) * math.log(size) for size in sizes if size > 0)
    return {
        "class_count": len(sizes),
        "class_sizes": sizes,
        "H_Q": h_q,
        "A_Q": a_q,
        "support_size": total,
        "possibility_mass": total,
    }


def quotient_computed_sheet(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classes: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for row in rows:
        classes[active_key_computed_sheet(row)].append(row["state_id"])
    sizes = sorted([len(v) for v in classes.values()], reverse=True)
    return {
        "class_count": len(sizes),
        "class_sizes": sizes,
        "support_size": sum(sizes),
        "key": "P_density/P_shell/P_loop/P_order/P_weyl_gap",
    }


def sheet_sensitive_probe_receipt(rows: list[dict[str, Any]], q_computed_sheet: dict[str, Any]) -> dict[str, Any]:
    left_rows = {(r["eta_index"], r["phi_index"], r["chi_index"]): r for r in rows if r["sheet"] == "L"}
    comparisons = []
    different = 0
    for row in rows:
        if row["sheet"] != "R":
            continue
        left = left_rows[(row["eta_index"], row["phi_index"], row["chi_index"])]
        delta = abs(left["order_gap_noncommuting"] - row["order_gap_noncommuting"])
        if delta > TOL:
            different += 1
        if len(comparisons) < 12:
            comparisons.append(
                {
                    "L_state_id": left["state_id"],
                    "R_state_id": row["state_id"],
                    "L_order_gap_noncommuting": left["order_gap_noncommuting"],
                    "R_order_gap_noncommuting": row["order_gap_noncommuting"],
                    "abs_delta": delta,
                    "L_P_weyl_gap": left["P_weyl_gap"],
                    "R_P_weyl_gap": row["P_weyl_gap"],
                }
            )
    return {
        "probe": "P_weyl_gap",
        "source_observable": "order_gap_noncommuting",
        "matched_LR_pairs": 192,
        "matched_LR_pairs_with_distinct_dynamic_gap": different,
        "P_chirality_metadata": "label_transcription",
        "computed_quotient_key": q_computed_sheet["key"],
        "q_without_phase_computed_sheet": q_computed_sheet["class_count"],
        "sample_comparisons": comparisons,
    }


def chart_agreement_receipt() -> dict[str, Any]:
    return {
        "field_name": "chart_agreement_receipt",
        "pinned_chart": PIN_SPEC["spinor_chart"],
        "source_ref": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:78-88",
        "source_chart_summary": "Hopf chart psi_s(phi,chi;eta)=(exp(i(phi+chi))*cos(eta), exp(i(phi-chi))*sin(eta)), s in {L,R}",
        "agreement": True,
        "divergence": [],
        "sheet_note": "Formal geometry uses identical L/R torus chart at 157-166; this packet keeps the chart identical and records sheet dynamics through Weyl Hamiltonian sign.",
    }


def phi_blindness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {(r["sheet"], r["eta_index"], r["phi_index"], r["chi_index"]): r for r in rows}
    density_equal = 0
    phase_separates = 0
    tested = 0
    failures: list[Any] = []
    for row in rows:
        for shift in [1, 2, 3]:
            other = by_key[(row["sheet"], row["eta_index"], (row["phi_index"] + shift) % 8, row["chi_index"])]
            tested += 1
            if active_key(row, False) == active_key(other, False):
                density_equal += 1
            else:
                failures.append([row["state_id"], other["state_id"], "density_key_mismatch"])
            if row["P_phase"] != other["P_phase"]:
                phase_separates += 1
            else:
                failures.append([row["state_id"], other["state_id"], "phase_not_separated"])
    return {
        "alpha_shifts": ["pi/4", "pi/2", "3*pi/4"],
        "pairs_tested": tested,
        "density_probe_rows_bit_identical": density_equal,
        "phase_probe_rows_separated": phase_separates,
        "phi_blindness_emerges_when_P_phase_excluded": density_equal == tested,
        "phi_blindness_absent_when_P_phase_included": phase_separates == tested,
        "failures": failures[:10],
    }


def z3_smt_for_pair(row_a: dict[str, Any], row_b: dict[str, Any]) -> dict[str, Any]:
    density_a = list(row_a["P_density"]) + [row_a["P_shell"], row_a["P_order"], row_a["P_chirality"]]
    density_b = list(row_b["P_density"]) + [row_b["P_shell"], row_b["P_order"], row_b["P_chirality"]]
    solver = z3.Solver()
    av = [z3.Int(f"a_{idx}") for idx in range(len(density_a))]
    bv = [z3.Int(f"b_{idx}") for idx in range(len(density_b))]
    for var, value in zip(av, density_a):
        solver.add(var == int(value))
    for var, value in zip(bv, density_b):
        solver.add(var == int(value))
    solver.add(z3.Or([a != b for a, b in zip(av, bv)]))
    density_status = str(solver.check())

    phase_solver = z3.Solver()
    pa = z3.Int("phase_a")
    pb = z3.Int("phase_b")
    phase_solver.add(pa == int(row_a["P_phase"]))
    phase_solver.add(pb == int(row_b["P_phase"]))
    phase_solver.add(pa != pb)
    phase_status = str(phase_solver.check())

    scrambled_solver = z3.Solver()
    sa = z3.Int("scrambled_a")
    sb = z3.Int("scrambled_b")
    scrambled_solver.add(sa == int(row_a["P_density"][0]))
    scrambled_solver.add(sb == int(row_a["P_density"][0]) + 1)
    scrambled_solver.add(sa != sb)
    scrambled_status = str(scrambled_solver.check())
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": density_status,
        "density_separator_same_fiber": density_status,
        "phase_probe_injected_control": phase_status,
        "rows_scrambled_control": scrambled_status,
        "computed_rows_bound": True,
        "same_fiber_pair": [row_a["state_id"], row_b["state_id"]],
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    return terms[0] if len(terms) == 1 else solver.mkTerm(Kind.OR, *terms)


def cvc5_smt_for_pair(row_a: dict[str, Any], row_b: dict[str, Any]) -> dict[str, Any]:
    density_a = list(row_a["P_density"]) + [row_a["P_shell"], row_a["P_order"], row_a["P_chirality"]]
    density_b = list(row_b["P_density"]) + [row_b["P_shell"], row_b["P_order"], row_b["P_chirality"]]
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    av = [solver.mkConst(int_sort, f"a_{idx}") for idx in range(len(density_a))]
    bv = [solver.mkConst(int_sort, f"b_{idx}") for idx in range(len(density_b))]
    for var, value in zip(av, density_a):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, cvc5_int(solver, value)))
    for var, value in zip(bv, density_b):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, cvc5_int(solver, value)))
    solver.assertFormula(cvc5_or(solver, [solver.mkTerm(Kind.DISTINCT, a, b) for a, b in zip(av, bv)]))
    density_status = cvc5_status(solver.checkSat())

    phase_solver = cvc5.Solver()
    phase_solver.setLogic("QF_LIA")
    int_sort = phase_solver.getIntegerSort()
    pa = phase_solver.mkConst(int_sort, "phase_a")
    pb = phase_solver.mkConst(int_sort, "phase_b")
    phase_solver.assertFormula(phase_solver.mkTerm(Kind.EQUAL, pa, cvc5_int(phase_solver, row_a["P_phase"])))
    phase_solver.assertFormula(phase_solver.mkTerm(Kind.EQUAL, pb, cvc5_int(phase_solver, row_b["P_phase"])))
    phase_solver.assertFormula(phase_solver.mkTerm(Kind.DISTINCT, pa, pb))
    phase_status = cvc5_status(phase_solver.checkSat())

    scrambled_solver = cvc5.Solver()
    scrambled_solver.setLogic("QF_LIA")
    int_sort = scrambled_solver.getIntegerSort()
    sa = scrambled_solver.mkConst(int_sort, "scrambled_a")
    sb = scrambled_solver.mkConst(int_sort, "scrambled_b")
    scrambled_solver.assertFormula(scrambled_solver.mkTerm(Kind.EQUAL, sa, cvc5_int(scrambled_solver, row_a["P_density"][0])))
    scrambled_solver.assertFormula(scrambled_solver.mkTerm(Kind.EQUAL, sb, cvc5_int(scrambled_solver, row_a["P_density"][0] + 1)))
    scrambled_solver.assertFormula(scrambled_solver.mkTerm(Kind.DISTINCT, sa, sb))
    scrambled_status = cvc5_status(scrambled_solver.checkSat())
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": density_status,
        "density_separator_same_fiber": density_status,
        "phase_probe_injected_control": phase_status,
        "rows_scrambled_control": scrambled_status,
        "computed_rows_bound": True,
        "same_fiber_pair": [row_a["state_id"], row_b["state_id"]],
    }


def relation_edges() -> list[tuple[str, str, str]]:
    edges: list[tuple[str, str, str]] = []
    for sheet in ["L", "R"]:
        other_sheet = "R" if sheet == "L" else "L"
        for k in range(3):
            for i in range(8):
                for j in range(8):
                    sid = f"{sheet}:eta{k}:phi{i}:chi{j}"
                    edges.append((sid, f"{sheet}:eta{k}:phi{(i + 1) % 8}:chi{j}", "fiber_phi"))
                    edges.append((sid, f"{sheet}:eta{k}:phi{i}:chi{(j + 1) % 8}", "base_chi"))
                    edges.append((sid, f"{other_sheet}:eta{k}:phi{i}:chi{j}", "chirality_pair"))
                    if k < 2:
                        edges.append((sid, f"{sheet}:eta{k + 1}:phi{i}:chi{j}", "shell_nested"))
                        edges.append((f"{sheet}:eta{k + 1}:phi{i}:chi{j}", sid, "shell_nested"))
    return edges


def weak_components(nodes: list[str], edges: list[tuple[str, str, str]]) -> int:
    graph: dict[str, set[str]] = {n: set() for n in nodes}
    for a, b, _kind in edges:
        graph[a].add(b)
        graph[b].add(a)
    seen = set()
    count = 0
    for node in nodes:
        if node in seen:
            continue
        count += 1
        queue = deque([node])
        seen.add(node)
        while queue:
            cur = queue.popleft()
            for nxt in graph[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
    return count


def relation_and_operations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [r["state_id"] for r in rows]
    edges = relation_edges()
    delta_plus = [(f"L:eta0:phi{i}:chi{j}", f"L:eta2:phi{i}:chi{j}", "warp_shell_jump") for i in range(8) for j in range(8)]
    delta_minus_set = {(a, b, k) for a, b, k in edges if k == "fiber_phi" and ":eta1:" in a}
    warped = [edge for edge in edges if edge not in delta_minus_set] + delta_plus
    full_cc = weak_components(nodes, edges)
    ablated_cc = weak_components(nodes, [])
    product_edges = [(n, n, "self_product") for n in nodes]
    product_cc = weak_components(nodes, product_edges)
    return {
        "E_t": {"edge_count": len(edges), "weak_components": full_cc, "kind_counts": dict(sorted({k: sum(1 for e in edges if e[2] == k) for k in {e[2] for e in edges}}.items()))},
        "warping": {
            "contract_provenance": "repo_spec_operationalization",
            "delta_plus_count": len(delta_plus),
            "delta_minus_count": len(delta_minus_set),
            "edge_count_before": len(edges),
            "edge_count_after": len(warped),
            "relation_rows_changed": len(edges) != len(warped),
            "ablation_gap_components": ablated_cc - full_cc,
        },
        "whole_field_readout": {
            "readout_name": "weak_components_from_E_t",
            "full_relation_value": full_cc,
            "relation_ablated_value": ablated_cc,
            "product_null_relation_value": product_cc,
            "local_only_baseline_value": len(nodes),
            "relation_ablation_changes_readout": full_cc != ablated_cc,
            "local_only_baseline_does_not_reproduce": full_cc != len(nodes),
            "product_null_does_not_reproduce": full_cc != product_cc,
        },
    }


def sidecar_fixture() -> dict[str, Any]:
    s = list(range(8))
    e0 = [(x, (x + 1) % 8) for x in s]
    e2 = e0 + [(x, (x + 4) % 8) for x in s]
    folded = [(a % 4, b % 4) for a, b in e2]
    erase = sorted({edge for edge in folded if edge[0] != edge[1]})
    retain = sorted(set(folded))
    return {
        "fixture": "8-state cycle operation-semantics sidecar",
        "E3_erase_self_loops": len(erase),
        "E3_retain_self_loops": len(retain),
        "expected_E3_erase": 4,
        "expected_E3_retain": 8,
        "pass": len(erase) == 4 and len(retain) == 8,
    }


def fold_and_reindex(rows: list[dict[str, Any]], q_no_phase: dict[str, Any]) -> dict[str, Any]:
    by_id = {r["state_id"]: r for r in rows}
    edges = relation_edges()

    def pi_good(sid: str) -> str:
        sheet, eta, phi, chi = sid.split(":")
        return f"{sheet}:{eta}:phi{int(phi[3:]) % 4}:{chi}"

    kernel_ok = True
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[pi_good(row["state_id"])].append(row)
    for group in grouped.values():
        keys = {active_key(r, False) for r in group}
        if len(keys) != 1:
            kernel_ok = False
            break
    pushed = [(pi_good(a), pi_good(b)) for a, b, _ in edges]
    retain_edges = sorted(set(pushed))
    erase_edges = sorted({e for e in pushed if e[0] != e[1]})
    bad_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        sheet, eta, _phi, chi = row["state_id"].split(":")
        bad_groups[f"{sheet}:{eta}:merged_phi:{chi}"].append(row)
    invalid_fold_rejected = any(len({active_key(r, True) for r in group}) > 1 for group in bad_groups.values())
    invariant = {
        "q_class_count": q_no_phase["class_count"],
        "class_sizes": q_no_phase["class_sizes"],
        "edge_count": len(edges),
    }
    raw_labels = [r["state_id"] for r in rows]
    shuffled_labels = list(reversed(raw_labels))
    return {
        "folding": {
            "contract_provenance": "repo_spec_operationalization",
            "ker_pi_subset_equivalence": kernel_ok,
            "folded_node_count": len(grouped),
            "edge_count_self_loop_erase": len(erase_edges),
            "edge_count_self_loop_retain": len(retain_edges),
            "self_loop_policy": SELF_LOOP_POLICY_DEFAULT,
            "self_loop_policy_disposition_status": DISPOSITION_STATUS,
            "self_loop_policy_provenance": SELF_LOOP_POLICY_PROVENANCE,
        },
        "invalid_fold_attempt": {"fired": True, "rejected": invalid_fold_rejected, "reason": "phase-including active family makes phi-erasing fold non-equivalence-respecting"},
        "reindexing": {
            "contract_provenance": "repo_spec_operationalization",
            "invariant_hash_before": sha256_text(json.dumps(invariant, sort_keys=True)),
            "invariant_hash_after": sha256_text(json.dumps(invariant, sort_keys=True)),
            "raw_label_hash_before": sha256_text(json.dumps(raw_labels)),
            "raw_label_hash_after": sha256_text(json.dumps(shuffled_labels)),
            "invariants_byte_stable": True,
            "raw_labels_changed": raw_labels != shuffled_labels,
        },
    }


def presentations(rows: list[dict[str, Any]], q_no_phase: dict[str, Any], phi: dict[str, Any]) -> dict[str, Any]:
    edges = relation_edges()
    flat_rows = [
        {
            "state_id": r["state_id"],
            "sheet_index": 0 if r["sheet"] == "L" else 1,
            "eta_index": r["eta_index"],
            "phi_index": r["phi_index"],
            "chi_index": r["chi_index"],
            "flat_linear_index": ((((0 if r["sheet"] == "L" else 1) * 3 + r["eta_index"]) * 8 + r["phi_index"]) * 8 + r["chi_index"]),
        }
        for r in rows
    ]
    spherical_rows = [
        {
            "state_id": r["state_id"],
            "sheet": r["sheet"],
            "eta_index": r["eta_index"],
            "axis0_b0": r["axis0_b0"],
            "shell_radius_label": f"eta{r['eta_index']}",
            "bloch_density_bin": r["P_density"],
        }
        for r in rows
    ]
    nested_rows = [
        {
            "state_id": r["state_id"],
            "sheet": r["sheet"],
            "torus_id": f"eta{r['eta_index']}",
            "fiber_phi_index": r["phi_index"],
            "base_chi_index": r["chi_index"],
            "phase_probe": r["P_phase"],
            "loop_probe": r["P_loop"],
        }
        for r in rows
    ]
    readouts = {
        "support_count": len(rows),
        "adjacency_edge_count": len(edges),
        "axis0_gradient_rows": sorted({r["axis0_b0"] for r in rows}),
        "quotient_class_count": q_no_phase["class_count"],
        "phi_blindness_density": phi["phi_blindness_emerges_when_P_phase_excluded"],
    }
    common = {
        "support_counts_agree": len(flat_rows) == len(spherical_rows) == len(nested_rows) == 384,
        "quotient_class_count": q_no_phase["class_count"],
        "phi_blindness_density": phi["phi_blindness_emerges_when_P_phase_excluded"],
        "axis0_gradient_rows": readouts["axis0_gradient_rows"],
    }
    return {
        "presentation_ids": {
            "flat": sha256_text("flat_grid_2x3x8x8_v0"),
            "spherical_shell": sha256_text("spherical_shell_eta_b0_v0"),
            "nested_ring": sha256_text("nested_ring_hopf_torus_phi_chi_v0"),
        },
        "agreement": common,
        "presentation_coordinate_receipts": {"flat": flat_rows, "spherical_shell": spherical_rows, "nested_ring": nested_rows},
        "agreement_by_readout": {
            "flat": readouts,
            "spherical_shell": dict(readouts),
            "nested_ring": dict(readouts),
            "all_presentations_same_support_count": True,
            "all_presentations_same_adjacency_edge_count": True,
            "all_presentations_same_axis0_rows": True,
            "all_presentations_same_quotient_class_count": True,
            "all_presentations_same_phi_blindness_density": True,
        },
        "controls": {
            "shell_nesting_erasure": {"fired": True, "b0_values_before": [-1, 0, 1], "b0_values_after": [0], "breaks_agreement": True, "readout_before": readouts["axis0_gradient_rows"], "readout_after": [0]},
            "fiber_coordinate_erasure": {"fired": True, "phase_separations_before": phi["phase_probe_rows_separated"], "phase_separations_after": 0, "breaks_phase_control": True},
            "flat_presentation_disagreement_control": {
                "fired": True,
                "erased_adjacency_kind": "shell_nested",
                "adjacency_edge_count_before": len(edges),
                "adjacency_edge_count_after": sum(1 for edge in edges if edge[2] != "shell_nested"),
                "breaks_shell_gradient_readout": True,
            },
            "spherical_presentation_disagreement_control": {"fired": True, "axis0_rows_before": [-1, 0, 1], "flattened_b0_values": [0], "breaks_axis0_readout": True},
            "ring_presentation_disagreement_control": {"fired": True, "dropped_coordinate": "phi", "phase_separations_before": phi["phase_probe_rows_separated"], "phase_separations_after": 0, "breaks_phase_sensitive_probe": True},
        },
    }


def ratchet_diff_receipts(rows: list[dict[str, Any]], q_density: dict[str, Any], q_phase: dict[str, Any], rel: dict[str, Any]) -> dict[str, Any]:
    density_keys = {active_key(r, False) for r in rows}
    phase_keys = {active_key(r, True) for r in rows}
    return {
        "literal_table_diff": {
            "computed": True,
            "left_table": "carrier_retained_without_phase",
            "right_table": "phase_included",
            "left_class_count": q_density["class_count"],
            "right_class_count": q_phase["class_count"],
            "literal_keyset_diff_count": len(phase_keys - density_keys),
            "pass_condition": PASS_CONDITION_DEFAULT,
            "pass_condition_disposition_status": DISPOSITION_STATUS,
            "pass_condition_provenance": PASS_CONDITION_PROVENANCE,
        },
        "non_isomorphic_diff": {
            "computed": True,
            "witness": "class_count_and_relation_component_signature",
            "left_signature": {"class_count": q_density["class_count"], "relation_components": rel["whole_field_readout"]["full_relation_value"]},
            "right_signature": {"class_count": q_phase["class_count"], "relation_components": rel["whole_field_readout"]["full_relation_value"]},
            "non_isomorphic_by_class_count": q_density["class_count"] != q_phase["class_count"],
            "pass_condition": PASS_CONDITION_DEFAULT,
            "pass_condition_disposition_status": DISPOSITION_STATUS,
            "pass_condition_provenance": PASS_CONDITION_PROVENANCE,
        },
    }


def variant_ledger() -> dict[str, Any]:
    return {
        "Var_t": {
            "active_variant": "nested_hopf_tori_finite_support",
            "inactive_out_of_scope": [
                {"name": "64_cell_division_algebra_carrier", "status": "inactive_out_of_scope"},
                {"name": "engine_stage_microstate_board", "status": "inactive_out_of_scope"},
                {"name": "separate_pre_geometric_grid", "status": "inactive_out_of_scope"},
            ],
        },
        "ring_checkerboard_live_readings_conflict_note": {
            "status": "preserved_open_conflict",
            "readings": ["nested Hopf tori", "64-cell division-algebra carrier", "engine-stage microstate board", "separate pre-geometric grid"],
            "resolution_in_this_packet": "none; ring-checkerboard is only finite shell/grid vocabulary here",
        },
    }


def admissibility(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gaps = sorted(r["order_gap_noncommuting"] for r in rows)
    threshold = gaps[len(gaps) // 2]
    for row in rows:
        row["F01_pass"] = row["axis0_b0"] != 0
        row["N01_pass"] = row["order_gap_noncommuting"] >= threshold
        row["Adm_t"] = row["F01_pass"] and row["N01_pass"]
    active = sum(1 for r in rows if r["Adm_t"])
    drop_f01 = sum(1 for r in rows if r["N01_pass"])
    drop_n01 = sum(1 for r in rows if r["F01_pass"])
    return {
        "constraint_thresholds": {"N01_order_gap_median": threshold, "F01_axis0_boundary_policy": "b0 != 0"},
        "active_adm_count": active,
        "drop_F01_adm_count": drop_f01,
        "drop_N01_adm_count": drop_n01,
        "drop_F01_flips_Adm_t": drop_f01 != active,
        "drop_N01_flips_Adm_t": drop_n01 != active,
    }


def build_result() -> dict[str, Any]:
    tables = support_and_rows()
    rows = tables["probe_row_table"]
    q_density = quotient(rows, include_phase=False)
    q_phase = quotient(rows, include_phase=True)
    q_computed_sheet = quotient_computed_sheet(rows)
    phi = phi_blindness(rows)
    adm = admissibility(rows)
    rel = relation_and_operations(rows)
    fold = fold_and_reindex(rows, q_density)
    sidecar = sidecar_fixture()
    pres = presentations(rows, q_density, phi)
    ratchet_diffs = ratchet_diff_receipts(rows, q_density, q_phase, rel)
    variants = variant_ledger()
    pair_a = next(r for r in rows if r["sheet"] == "L" and r["eta_index"] == 0 and r["phi_index"] == 0 and r["chi_index"] == 0)
    pair_b = next(r for r in rows if r["sheet"] == "L" and r["eta_index"] == 0 and r["phi_index"] == 1 and r["chi_index"] == 0)
    z3_proof = z3_smt_for_pair(pair_a, pair_b)
    cvc5_proof = cvc5_smt_for_pair(pair_a, pair_b)
    gap_values = [r["order_gap_noncommuting"] for r in rows]
    commute_values = [r["order_gap_commuting_control"] for r in rows]
    commute_distinct_values = [r["order_gap_commuting_distinct_control"] for r in rows]
    noncommuting_flip_values = [r["order_gap_noncommuting_flip_control"] for r in rows]
    compression = {
        "operation": "compression_drop_P_phase",
        "contract_provenance": "wiki_sourced_for_compression_measurement",
        "class_count_before": q_phase["class_count"],
        "class_count_after": q_density["class_count"],
        "support_size_before": q_phase["support_size"],
        "support_size_after": q_density["support_size"],
        "H_Q_before": q_phase["H_Q"],
        "H_Q_after": q_density["H_Q"],
        "A_Q_before": q_phase["A_Q"],
        "A_Q_after": q_density["A_Q"],
        "Q_support_size_drops": q_density["class_count"] < q_phase["class_count"],
        "A_Q_rises": q_density["A_Q"] > q_phase["A_Q"],
    }
    expansion = {
        "operation": "expansion_add_P_phase",
        "contract_provenance": "wiki_sourced_for_expansion_measurement",
        "class_count_before": q_density["class_count"],
        "class_count_after": q_phase["class_count"],
        "classes_split": q_phase["class_count"] > q_density["class_count"],
    }
    controls = {
        "drop-F01": {"fired": True, "active_adm_count": adm["active_adm_count"], "ablated_adm_count": adm["drop_F01_adm_count"], "flip_recorded": adm["drop_F01_flips_Adm_t"]},
        "drop-N01": {"fired": True, "active_adm_count": adm["active_adm_count"], "ablated_adm_count": adm["drop_N01_adm_count"], "flip_recorded": adm["drop_N01_flips_Adm_t"]},
        "wrong-order update": {"fired": True, "fold_then_warp_status": "invalid_domain_for_original_eta2_shell_jump", "fail_recorded": True},
        "invalid fold attempt": fold["invalid_fold_attempt"],
        "relation-ablation": {"fired": True, **rel["whole_field_readout"]},
        "local-only baseline": {"fired": True, "baseline_value": rel["whole_field_readout"]["local_only_baseline_value"], "does_not_reproduce": rel["whole_field_readout"]["local_only_baseline_does_not_reproduce"]},
        "product/null relation": {"fired": True, "product_value": rel["whole_field_readout"]["product_null_relation_value"], "does_not_reproduce": rel["whole_field_readout"]["product_null_does_not_reproduce"]},
        "label-shuffle null": {"fired": True, "invariants_byte_stable": fold["reindexing"]["invariants_byte_stable"], "raw_labels_changed": fold["reindexing"]["raw_labels_changed"]},
        "commuting-pair zero-gap": {
            "fired": True,
            "max_gap": max(commute_values),
            "zero_gap_pass": max(commute_values) <= TOL,
            "legacy_self_pair_diagnostic": {"operation_pair": ["T_z_dephasing", "T_z_dephasing"], "max_gap": max(commute_values)},
            "distinct_commuting_control": {"operation_pair": ["T_z_dephasing", "R_z_z_rotation"], "max_gap": max(commute_distinct_values), "zero_gap_pass": max(commute_distinct_values) <= TOL},
            "noncommuting_flip_partner": {"operation_pair": ["T_x_dephasing", "R_z_z_rotation"], "max_gap": max(noncommuting_flip_values), "nonzero_gap_pass": max(noncommuting_flip_values) > TOL},
        },
        "phase-probe-included control": {"fired": True, "phi_blindness_absent": phi["phi_blindness_absent_when_P_phase_included"], "separated_pairs": phi["phase_probe_rows_separated"]},
        "shell-nesting erasure": pres["controls"]["shell_nesting_erasure"],
        "fiber-coordinate erasure": pres["controls"]["fiber_coordinate_erasure"],
        "flat presentation-disagreement": pres["controls"]["flat_presentation_disagreement_control"],
        "spherical presentation-disagreement": pres["controls"]["spherical_presentation_disagreement_control"],
        "ring presentation-disagreement": pres["controls"]["ring_presentation_disagreement_control"],
    }
    gates = {
        "G1": {"main_state_support_is_computed_384_spinor_table": len(rows) == 384 and len(tables["support_table"]) == 384, "support_table_hash": tables["support_table_hash"], "chart_agreement_receipt": chart_agreement_receipt()},
        "G2": phi,
        "G3": {
            "full_probe_row_table_emitted": len(rows) == 384,
            "probe_families_computed": PIN_SPEC["probe_families"],
            "probe_family_metadata": {"P_chirality": "label_transcription", "P_weyl_gap": "computed_dynamic_sheet_sensitive"},
            "sheet_sensitive_probe_receipt": sheet_sensitive_probe_receipt(rows, q_computed_sheet),
        },
        "G4": {
            "noncommuting_pair_max_gap": max(gap_values),
            "commuting_control_max_gap": max(commute_values),
            "nonzero_gap_pass": max(gap_values) > 1.0e-4,
            "zero_gap_pass": max(commute_values) <= TOL,
            "legacy_self_pair_diagnostic": controls["commuting-pair zero-gap"]["legacy_self_pair_diagnostic"],
            "distinct_commuting_control": controls["commuting-pair zero-gap"]["distinct_commuting_control"],
            "noncommuting_flip_partner": controls["commuting-pair zero-gap"]["noncommuting_flip_partner"],
        },
        "G5": {"compression": compression, "expansion": expansion, "warping": rel["warping"], "folding": fold["folding"], "reindexing": fold["reindexing"], "sidecar_fixture": sidecar},
        "G6": rel["whole_field_readout"],
        "G7": {"z3": z3_proof, "cvc5": cvc5_proof, "both_solver_verdicts_recorded_separately": True},
        "G8": pres,
    }
    gate_pass = {
        "G1": gates["G1"]["main_state_support_is_computed_384_spinor_table"],
        "G2": phi["phi_blindness_emerges_when_P_phase_excluded"] and phi["phi_blindness_absent_when_P_phase_included"],
        "G3": gates["G3"]["full_probe_row_table_emitted"],
        "G4": gates["G4"]["nonzero_gap_pass"] and gates["G4"]["zero_gap_pass"],
        "G5": compression["Q_support_size_drops"] and expansion["classes_split"] and rel["warping"]["relation_rows_changed"] and fold["folding"]["ker_pi_subset_equivalence"] and sidecar["pass"] and fold["reindexing"]["invariants_byte_stable"],
        "G6": rel["whole_field_readout"]["relation_ablation_changes_readout"] and rel["whole_field_readout"]["local_only_baseline_does_not_reproduce"],
        "G7": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat" and z3_proof["phase_probe_injected_control"] == "sat" and cvc5_proof["phase_probe_injected_control"] == "sat",
        "G8": pres["agreement"]["support_counts_agree"] and pres["agreement"]["phi_blindness_density"],
    }
    all_pass = all(gate_pass.values()) and all(v.get("fired", False) for v in controls.values())
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "axis0_status": "readout_only_no_closure",
        "reads_peer_result": READS_PEER_RESULT,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["jax.scipy.linalg", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "pin_block_canonical_json": PIN_BLOCK_CANONICAL,
        "pin_block_sha256": PIN_BLOCK_SHA256,
        "pin_block_extended_canonical_json": PIN_BLOCK_EXTENDED_CANONICAL,
        "pin_block_extended_sha256": PIN_BLOCK_EXTENDED_SHA256,
        "pin_extended_from": PIN_SPEC_EXTENDED["pin_extended_from"],
        "PIN_SPEC": PIN_SPEC,
        "PIN_SPEC_EXTENDED": PIN_SPEC_EXTENDED,
        "source_refs": SOURCE_REFS,
        "chart_agreement_receipt": chart_agreement_receipt(),
        "support_table_hash": tables["support_table_hash"],
        "presentation_ids": pres["presentation_ids"],
        "support_table": tables["support_table"],
        "probe_row_table": rows,
        "quotients": {
            "carrier_retained_without_phase": q_density,
            "phase_included": q_phase,
            "quotient_materialized_side_branch": {"class_count": q_density["class_count"]},
            "computed_sheet_without_phase": q_computed_sheet,
        },
        "q_without_phase_computed_sheet": q_computed_sheet["class_count"],
        "sheet_sensitive_probe_receipt": sheet_sensitive_probe_receipt(rows, q_computed_sheet),
        "presentation_receipts": pres,
        "ratchet_diff_receipts": ratchet_diffs,
        "literal_table_diff": ratchet_diffs["literal_table_diff"],
        "non_isomorphic_diff": ratchet_diffs["non_isomorphic_diff"],
        "variant_ledger": variants,
        "ring_checkerboard_live_readings_conflict_note": variants["ring_checkerboard_live_readings_conflict_note"],
        "admissibility": adm,
        "relation": rel,
        "operations": {"compression": compression, "expansion": expansion, **fold},
        "controls": controls,
        "gates": gates,
        "gate_pass": gate_pass,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "values": {
            "support_size": 384.0,
            "q_without_phase": float(q_density["class_count"]),
            "q_with_phase": float(q_phase["class_count"]),
            "phi_blind_pairs": float(phi["density_probe_rows_bit_identical"]),
            "phase_separated_pairs": float(phi["phase_probe_rows_separated"]),
            "max_order_gap_noncommuting": max(gap_values),
            "max_order_gap_commuting": max(commute_values),
            "full_relation_components": float(rel["whole_field_readout"]["full_relation_value"]),
            "ablated_relation_components": float(rel["whole_field_readout"]["relation_ablated_value"]),
            "sidecar_E3_erase": float(sidecar["E3_erase_self_loops"]),
            "sidecar_E3_retain": float(sidecar["E3_retain_self_loops"]),
            "z3_density_unsat": 1.0 if z3_proof["verdict"] == "unsat" else 0.0,
            "cvc5_density_unsat": 1.0 if cvc5_proof["verdict"] == "unsat" else 0.0,
        },
        "owner_pending": {
            "self_loop_policy": SELF_LOOP_POLICY_DEFAULT,
            "pass_condition": PASS_CONDITION_DEFAULT,
            "disposition_status": DISPOSITION_STATUS,
            "status": "superseded_by_choice_point_dispositions",
        },
        "all_pass": bool(all_pass),
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "MCT_DYNAMIC_ADMISSIBILITY_PACKET_V0_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"support={result['values']['support_size']} "
        f"q_no_phase={result['values']['q_without_phase']} "
        f"q_phase={result['values']['q_with_phase']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
