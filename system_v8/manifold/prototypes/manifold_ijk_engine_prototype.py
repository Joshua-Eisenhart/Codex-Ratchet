#!/usr/bin/env python3
"""Finite IJK entropic-geometry and paired-engine prototype.

This is deliberately a constructive simulation.  It does not ask the Ratchet
to derive the unique carrier before the proposed carrier is allowed to run.
"""

from __future__ import annotations

import argparse
import cmath
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


HERE = Path(__file__).resolve().parent
SHELLS = 3
ANGLES = 8
N = SHELLS * ANGLES
HORIZON = 4


def idx(shell: int, angle: int) -> int:
    return shell * ANGLES + (angle % ANGLES)


def cell(index: int) -> tuple[int, int]:
    return divmod(index, ANGLES)


def zeros_matrix() -> list[list[complex]]:
    return [[0j for _ in range(N)] for _ in range(N)]


def identity_matrix() -> list[list[complex]]:
    out = zeros_matrix()
    for i in range(N):
        out[i][i] = 1.0
    return out


def matmul(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    out = zeros_matrix()
    for i in range(N):
        for k in range(N):
            aik = a[i][k]
            if abs(aik) < 1e-15:
                continue
            for j in range(N):
                if abs(b[k][j]) >= 1e-15:
                    out[i][j] += aik * b[k][j]
    return out


def matvec(a: list[list[complex]], v: list[complex]) -> list[complex]:
    return [sum(a[i][j] * v[j] for j in range(N)) for i in range(N)]


def frobenius(a: list[list[complex]], b: list[list[complex]]) -> float:
    return math.sqrt(sum(abs(a[i][j] - b[i][j]) ** 2 for i in range(N) for j in range(N)))


def normalize(v: list[complex]) -> list[complex]:
    norm = math.sqrt(sum(abs(x) ** 2 for x in v))
    if norm < 1e-15:
        return [1.0 + 0j] + [0j] * (N - 1)
    return [x / norm for x in v]


def probabilities(v: list[complex]) -> list[float]:
    total = sum(abs(x) ** 2 for x in v)
    return [abs(x) ** 2 / total for x in v]


def shannon_bits(p: list[float]) -> float:
    return -sum(x * math.log2(x) for x in p if x > 1e-15)


def path_operator(hand: int) -> list[list[complex]]:
    """Finite opening/path-sum operator on an angular ring of radial shells."""
    out = zeros_matrix()
    phase = math.pi / 7
    for s in range(SHELLS):
        for a in range(ANGLES):
            src = idx(s, a)
            edges = [
                (s, a, 0.36, 0.0),
                (s, a + hand, 0.62, hand * phase),
                (s, a - hand, 0.31, -hand * phase / 2),
            ]
            if s + 1 < SHELLS:
                edges.append((s + 1, a + hand, 0.47, hand * phase * (s + 1)))
            if s > 0:
                edges.append((s - 1, a, 0.23, -hand * phase * s / 2))
            scale = math.sqrt(sum(weight * weight for _, _, weight, _ in edges))
            for ds, da, weight, edge_phase in edges:
                out[idx(ds, da)][src] += (weight / scale) * cmath.exp(1j * edge_phase)
    return out


def binding_operator(hand: int) -> list[list[complex]]:
    """A finite geometry-dependent settlement; it narrows without deleting all fuzz."""
    out = zeros_matrix()
    for s in range(SHELLS):
        for a in range(ANGLES):
            parity = (a + s + (0 if hand > 0 else 1)) % 4
            weight = (1.0, 0.82, 0.56, 0.34)[parity]
            out[idx(s, a)][idx(s, a)] = weight
    return out


def twist_operator(hand: int) -> list[list[complex]]:
    out = identity_matrix()
    for s in range(SHELLS):
        for a in range(ANGLES):
            theta = hand * (a + 1) * (s + 1) * math.pi / 32
            out[idx(s, a)][idx(s, a)] = cmath.exp(1j * theta)
    return out


def coarse_projection(matrix: list[list[complex]], threshold: float = 0.12) -> list[list[complex]]:
    """Lossy settlement used only for the effective associator witness."""
    return [[z if abs(z) >= threshold else 0j for z in row] for row in matrix]


def apply(op: list[list[complex]], state: list[complex]) -> list[complex]:
    return normalize(matvec(op, state))


def axis0_ijk(state: list[complex], hand: int) -> list[dict]:
    """Return the full local I/J/K cofield; do not scalarize it."""
    field = []
    for s in range(SHELLS):
        for a in range(ANGLES):
            here = state[idx(s, a)]
            cw = state[idx(s, a + hand)]
            ccw = state[idx(s, a - hand)]
            outer = state[idx(min(s + 1, SHELLS - 1), a)]
            inner = state[idx(max(s - 1, 0), a)]
            i_component = abs(outer) ** 2 - abs(inner) ** 2
            j_component = here.conjugate() * (cw - ccw)
            k_component = here.conjugate() * (outer - inner)
            field.append({
                "shell": s,
                "angle": a,
                "i": i_component,
                "j": [j_component.real, j_component.imag],
                "k": [k_component.real, k_component.imag],
            })
    return field


def finite_path_sum(start: int, hand: int, horizon: int = HORIZON) -> dict:
    """Enumerate a bounded Feynman-style sum and its incoherent control."""
    op = path_operator(hand)
    coherent: dict[int, complex] = defaultdict(complex)
    incoherent: dict[int, float] = defaultdict(float)
    path_count = 0

    def walk(node: int, depth: int, amplitude: complex) -> None:
        nonlocal path_count
        if depth == horizon:
            coherent[node] += amplitude
            incoherent[node] += abs(amplitude) ** 2
            path_count += 1
            return
        for target in range(N):
            edge = op[target][node]
            if abs(edge) >= 1e-15:
                walk(target, depth + 1, amplitude * edge)

    walk(start, 0, 1.0 + 0j)
    coherent_weights = {end: abs(amp) ** 2 for end, amp in coherent.items()}
    c_total = sum(coherent_weights.values())
    i_total = sum(incoherent.values())
    return {
        "horizon": horizon,
        "path_count": path_count,
        "endpoint_count": len(coherent),
        "hartley_path_capacity_bits": math.log2(path_count),
        "coherent_endpoint_probabilities": {
            str(end): weight / c_total for end, weight in sorted(coherent_weights.items())
        },
        "incoherent_endpoint_probabilities": {
            str(end): weight / i_total for end, weight in sorted(incoherent.items())
        },
        "interference_l1": sum(
            abs(coherent_weights.get(end, 0.0) / c_total - incoherent.get(end, 0.0) / i_total)
            for end in set(coherent_weights) | set(incoherent)
        ),
    }


@dataclass
class EngineResult:
    name: str
    hand: int
    precedence: str
    ticks: int
    final_probabilities: list[float]
    entropy_trace_bits: list[float]
    dominant_trace: list[int]
    axis0_ijk_final: list[dict]
    circulation: float


def run_engine(hand: int, ticks: int = 48, start: int = 0) -> EngineResult:
    opening = path_operator(hand)
    binding = binding_operator(hand)
    twist = twist_operator(hand)
    state = [0j] * N
    state[start] = 1.0 + 0j
    entropy_trace = []
    dominant_trace = []
    circulation = 0.0
    for _ in range(ticks):
        old_p = probabilities(state)
        if hand < 0:
            # Binding-before-opening / compressor-oriented hand.
            state = apply(binding, state)
            state = apply(opening, state)
        else:
            # Opening-before-binding / expander-oriented hand.
            state = apply(opening, state)
            state = apply(binding, state)
        state = apply(twist, state)
        new_p = probabilities(state)
        for index, mass in enumerate(new_p):
            _, a = cell(index)
            circulation += hand * mass * ((a - cell(max(range(N), key=old_p.__getitem__))[1]) % ANGLES)
        entropy_trace.append(shannon_bits(new_p))
        dominant_trace.append(max(range(N), key=new_p.__getitem__))
    return EngineResult(
        name="TYPE_1_BIND_OPEN" if hand < 0 else "TYPE_2_OPEN_BIND",
        hand=hand,
        precedence="BIND->OPEN" if hand < 0 else "OPEN->BIND",
        ticks=ticks,
        final_probabilities=probabilities(state),
        entropy_trace_bits=entropy_trace,
        dominant_trace=dominant_trace,
        axis0_ijk_final=axis0_ijk(state, hand),
        circulation=circulation,
    )


def basin_scan(hand: int) -> dict:
    signatures: dict[int, list[int]] = defaultdict(list)
    for start in range(N):
        result = run_engine(hand, ticks=36, start=start)
        signature = result.dominant_trace[-1]
        signatures[signature].append(start)
    return {
        "terminal_dominant_signatures": {
            str(signature): starts for signature, starts in sorted(signatures.items())
        },
        "basin_count_at_declared_resolution": len(signatures),
        "basin_sizes": sorted(len(starts) for starts in signatures.values()),
        "note": "These are finite dominant-state basins at the declared 36-tick/readout resolution, not a theorem about continuum attractors.",
    }


def svg(left: EngineResult, right: EngineResult) -> str:
    width, height = 900, 340
    panels = [(left, 30), (right, 470)]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#0c1020"/>']
    for result, x0 in panels:
        parts.append(f'<text x="{x0}" y="30" fill="#f2f5ff" font-family="sans-serif" font-size="18">{result.name}: {result.precedence}</text>')
        pmax = max(result.final_probabilities)
        for s in range(SHELLS):
            parts.append(f'<text x="{x0}" y="{78+s*72}" fill="#aab3ce" font-family="sans-serif" font-size="13">shell {s}</text>')
            for a in range(ANGLES):
                p = result.final_probabilities[idx(s, a)] / pmax
                red = int(40 + 200 * p)
                green = int(65 + 130 * (1-p))
                blue = int(120 + 120 * (1-p))
                x, y = x0 + 58 + a * 43, 52 + s * 72
                parts.append(f'<rect x="{x}" y="{y}" width="37" height="50" rx="6" fill="rgb({red},{green},{blue})"/>')
                parts.append(f'<text x="{x+18.5}" y="{y+30}" text-anchor="middle" fill="white" font-family="monospace" font-size="10">{result.final_probabilities[idx(s,a)]:.2f}</text>')
    parts.append('<text x="30" y="322" fill="#8892ad" font-family="sans-serif" font-size="12">Finite ring-shell probability fields; each row wraps angularly. I/J/K cofield values remain in RUN_RECEIPT.json.</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=HERE,
        help="directory for the report, receipt, and SVG (default: source directory)",
    )
    args = parser.parse_args(argv)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    left = run_engine(-1)
    right = run_engine(+1)
    opening = path_operator(+1)
    binding = binding_operator(+1)
    twist = twist_operator(+1)
    counter_opening = path_operator(-1)

    noncomm_gap = frobenius(matmul(binding, opening), matmul(opening, binding))
    # Three distinct deformations in fixed order: positive opening, binding,
    # and counter-oriented opening.  The binary effective product includes a
    # declared lossy settlement P.  Exact matrix multiplication remains
    # associative; (A star B) star C != A star (B star C) measures only the
    # effective bracket sensitivity introduced by P.
    left_bracket = coarse_projection(matmul(coarse_projection(matmul(opening, binding)), counter_opening))
    right_bracket = coarse_projection(matmul(opening, coarse_projection(matmul(binding, counter_opening))))
    associator_gap = frobenius(left_bracket, right_bracket)
    chiral_gap = math.sqrt(sum((a-b) ** 2 for a, b in zip(left.final_probabilities, right.final_probabilities)))
    path_left = finite_path_sum(idx(0, 0), -1)
    path_right = finite_path_sum(idx(0, 0), +1)

    checks = {
        "finite_carrier": N == 24,
        "both_engines_ran": left.ticks == right.ticks == 48,
        "noncommutation_observed": noncomm_gap > 1e-6,
        "effective_bracket_sensitivity_observed": associator_gap > 1e-6,
        "chiral_outputs_distinguished": chiral_gap > 1e-6,
        "finite_path_interference_observed": path_left["interference_l1"] > 1e-6 and path_right["interference_l1"] > 1e-6,
        "ijk_not_scalarized": any(abs(x["i"]) > 1e-12 or abs(complex(*x["j"])) > 1e-12 or abs(complex(*x["k"])) > 1e-12 for x in left.axis0_ijk_final),
    }
    receipt = {
        "status": "EXECUTED_AUTHORED_PROTOTYPE_NOT_UNIQUE_DERIVATION",
        "gate_policy": "REPORT_ALL_RESULTS; CHECKS_DO_NOT_BLOCK_EXECUTION",
        "carrier": {
            "name": "finite ring-of-fuzz-shells path complex",
            "shells": SHELLS,
            "angles_per_shell": ANGLES,
            "cells": N,
            "axis0_type": "local I/J/K cofield over every cell; scalar entropy readouts are diagnostics only",
        },
        "math": {
            "finite_path_update": "psi_next(v)=normalize(sum_u W_chi(v,u) psi(u)); binding and twist composed in opposite precedence by the two hands",
            "noncommutator_frobenius": noncomm_gap,
            "effective_lossy_associator_frobenius": associator_gap,
            "associator_word": "(OPEN_PLUS star BIND_PLUS) star OPEN_MINUS versus OPEN_PLUS star (BIND_PLUS star OPEN_MINUS)",
            "chiral_final_probability_l2": chiral_gap,
        },
        "finite_path_sums": {"left": path_left, "right": path_right},
        "engines": {"left": asdict(left), "right": asdict(right)},
        "basins": {"left": basin_scan(-1), "right": basin_scan(+1)},
        "checks": checks,
        "interpretation_lock": {
            "noncommutation": "measured in this authored carrier",
            "nonassociativity": "effective bracket sensitivity from declared lossy settlement; not proof of intrinsic nonassociative algebra",
            "chirality": "opposite handed schedules and phases produce distinguishable outputs in this carrier",
            "axis0": "I/J/K field is primary; Shannon and Hartley scalars do not replace it",
        },
    }
    raw = json.dumps(receipt, indent=2, sort_keys=True)
    receipt["receipt_sha256_before_hash_field"] = hashlib.sha256(raw.encode()).hexdigest()
    receipt_path = output_dir / "RUN_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    (output_dir / "engine_field.svg").write_text(svg(left, right) + "\n")

    report = rf"""# IJK manifold and paired-engine prototype result

Status: **{receipt['status']}**

This run does what the prototype request requires: it authors one constrained
finite entropic geometry, runs both engine hands through it, and reports the
behavior.  It does not wait for a unique Ratchet derivation.

## What ran

- finite carrier: {SHELLS} shells x {ANGLES} angular cells = {N} cells;
- Axis 0: a local `i/j/k` cofield on all {N} cells;
- bounded path sums: {path_left['path_count']} left-hand and {path_right['path_count']} right-hand length-{HORIZON} paths from one seed;
- two engines: `{left.precedence}` and `{right.precedence}`, {left.ticks} ticks each;
- authored basin scan: every one of the {N} basis starts, run for 36 ticks.

## Direct measurements

| Measurement | Value | Meaning in this prototype |
|---|---:|---|
| Noncommutator norm | {noncomm_gap:.8f} | Opening and binding order changes the finite operator. |
| Effective associator norm | {associator_gap:.8f} | The declared lossy settlement makes bracket placement matter. |
| Chiral output distance | {chiral_gap:.8f} | The two handed engine fields finish differently. |
| Left finite-path interference | {path_left['interference_l1']:.8f} | Coherent path addition differs from the incoherent control. |
| Right finite-path interference | {path_right['interference_l1']:.8f} | Same test for the opposite hand. |
| Left final Shannon diagnostic | {left.entropy_trace_bits[-1]:.8f} bits | A readout of the final field, not Axis 0 itself. |
| Right final Shannon diagnostic | {right.entropy_trace_bits[-1]:.8f} bits | A readout of the final field, not Axis 0 itself. |

## Basin readout

- left dominant-state basins at the declared resolution: {receipt['basins']['left']['basin_count_at_declared_resolution']}, sizes {receipt['basins']['left']['basin_sizes']};
- right dominant-state basins: {receipt['basins']['right']['basin_count_at_declared_resolution']}, sizes {receipt['basins']['right']['basin_sizes']}.

These basin counts are results of this exact authored update and readout.  They
are not promoted as the universe's canonical basin count.

## The corrected Axis-0 meaning

At a cell `(shell, angle)` the run records

\[
\mathcal A_0(x)=i(x)\,\mathbf e_i+j(x)\,\mathbf e_j+k(x)\,\mathbf e_k.
\]

Here `i` is longitudinal opening/binding flux, `j` is oriented angular path
amplitude, and `k` is transverse inter-shell fuzz amplitude.  The full field
over all cells is Axis 0 in this implementation hypothesis.  A capacity or
Shannon number is only a projection of that field.

## Claim ceiling

The run shows that the proposed ingredients can coexist in one functioning
finite simulation: `i/j/k` Axis 0, fuzz shells, finite path interference,
noncommuting deformation order, effective bracket sensitivity, chirality,
basin readouts, and both engines.  It does not show that this discretization is
unique, that nonassociativity is intrinsic rather than settlement-induced, or
that the resulting numbers are physical constants.

All checks are present in `RUN_RECEIPT.json`.  They report the behavior and do
not gate whether the model is allowed to run.
"""
    (output_dir / "RESULT.md").write_text(report)
    print(json.dumps({"checks": checks, "receipt": str(receipt_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
