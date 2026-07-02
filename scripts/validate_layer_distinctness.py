#!/usr/bin/env python3
"""Fail closed on layer-lego numeric theater.

This gate is complementary to ``validate_layer_completion_claims.py`` (which
blocks scout receipts narrated as completion) and ``validate_formal_scout_results.py``
(which checks receipt section structure). It checks the thing those two cannot:
whether the per-layer numbers are *real per-layer work* or shared-scaffold theater.

It was specified from the 2026-05-28 deep audit (four recurring shortcut patterns at
fixed source lines) and then hardened by a 2026-05-28 fresh-context audit of this very
gate, which found that an earlier version only inspected ``summary`` and was therefore
*bypassed* by the ``layer_l4_l5_l7_individual_runner`` receipts, which park their real
gaps in ``graveyard_companions`` / ``controls.positive`` / ``rows[].layer_gate`` and emit
a bookkeeping-only ``summary``. This version is location-agnostic.

HARD patterns (block):
  1. cross_layer_signature_identity   -- distinct layers emit an identical claim signature.
  2. fabricated/vacuous tool ablation  -- ``control_gap_after_stub`` hardcoded 0.0 so
                                          delta==before; or ``non_vacuous:true`` with no
                                          numeric witness; or a witness whose only gap is
                                          below GAP_FLOOR; or a witness that echoes a
                                          claim-bearing baseline with no after-removal value.
  3. vacuous_scale_ladder              -- a claim-physics key frozen across >=2 site counts
                                          (unless the receipt explicitly declares it invariant).
  4. vacuous_claim_bearing_control     -- a *positive* claim witness gap below GAP_FLOOR
                                          (a claim with no signal), not honestly fenced.
  5. insufficient_nonvacuous_controls  -- fewer than MIN_NONVACUOUS_CONTROLS distinct real
                                          claim controls (the "fence everything" dodge).
  6. no_observable_signature           -- a layer receipt that exposes no claim-bearing
                                          signature at all (absence is not a pass).

SOFT (report, non-blocking): vacuous_control_fenced, collapsed_controls,
vacuous_negative_control, shared_dimension_constant, declared_invariant_scale.

A layer "passes the distinctness gate" iff zero HARD violations across its receipts AND
no cross-layer collision. The HARD count is NOT a genuineness ranking on its own -- read
``observable_surface``/``rankable`` in the scoreboard: a layer with low HARD but low
observable surface is UNKNOWN, not clean. The gate proves nothing about correctness; it
only refuses to let theater pass.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_DIR = ROOT / "system_v5" / "ops" / "formal_scouts" / "results"

GAP_FLOOR = 1e-5              # below this a gap is vacuous (matches probe GAP_FLOOR)
SIG_TOL = 1e-6               # two numbers count as identical within this absolute tolerance
MIN_NONVACUOUS_CONTROLS = 3  # distinct real claim controls a layer must carry (see docs below)
MIN_SIGNATURE_TERMS = 2      # a signature needs at least this many numbers to be comparable

# Why 3: a real layer claim is defended by, at minimum, an order/sequence control, a
# label/identity control, and a carrier-erasure control -- three independent ways the claim
# can die. Fewer than that and a layer cannot distinguish itself from a relabel. The check
# is suppressed when the only reason the count fell short is collapsed_controls (already
# flagged), to avoid double-penalising one fact.

# Layer id from filename: r0 root, or l0..l13 (the noncommutative-order stack registry).
LAYER_RE = re.compile(r"^(r0|l(?:1[0-3]|[0-9]))_", re.IGNORECASE)

VARIANTS = (
    ("full_spinor_network", "full_spinor_network"),
    ("peps3d_bond4_tool_ablation", "bond4"),
    ("mps_peps2d_peps3d_depth", "depth"),
)

GAP_KEY_RE = re.compile(r"gap", re.IGNORECASE)

# Summary keys that are bookkeeping, not part of a numeric fingerprint or an echo baseline.
NON_SIGNATURE_KEYS = {
    "elapsed_seconds", "max_sites", "max_qubits", "max_peps3d_bond", "max_peps2d_bond",
    "max_peps3d_sites", "layer", "site_count", "n_sites", "sites", "count", "bond_dim",
    "bond_dims", "site_counts", "max_bond", "version", "tier", "row_count", "shell_count",
    "phase_grid_count", "cell_count", "edge_count", "face_count", "vertex_count",
}

# Row fields that legitimately grow with N (structural), excluded from scale comparison.
STRUCTURAL_ROW_KEYS = {
    "site_count", "sites", "max_sites", "max_qubits", "qubits", "cell_count",
    "edge_count", "face_count", "vertex_count", "peps3d_bond_dim", "peps2d_bond_dim",
    "bond_dim", "shape", "dense_state_dimension_if_used", "n", "depth", "row_count",
}

# A claim-bearing physics quantity (entropy / information / gap / topological invariant).
PHYSICS_KEY_RE = re.compile(
    r"(entropy|mutual_information|gap|negativity|coherent_information|"
    r"conditional_entropy|renyi|distance|signature|chirality|"
    r"holonomy|flux|curvature|coupling|winding|chern)",
    re.IGNORECASE,
)

# Keys whose N-invariance can be sound (declared topological invariants).
INVARIANT_KEY_RE = re.compile(r"(invariant|winding|chern)", re.IGNORECASE)

# Matched-control / erasure / equivariance legs co-located inside positive witness blocks.
# These are *intended* to collapse toward zero (erase X, X-signal vanishes), so a 0.0 here is
# the opposite of theater -- UNLESS the receipt declares the erasure load-bearing (then a 0.0
# means the defining feature did not actually matter, which is theater).
ERASURE_KEY_RE = re.compile(r"(eras|equivarian|commut|collaps|scrambl|shuffl)", re.IGNORECASE)

LN8 = math.log(8.0)


@dataclass
class Violation:
    code: str
    severity: str           # "HARD" or "SOFT"
    detail: str
    layer: str | None = None
    path: str | None = None


@dataclass
class Receipt:
    path: Path
    layer: str | None
    variant: str
    data: Any
    signature: dict[str, float] = field(default_factory=dict)


# --------------------------------------------------------------------------- helpers


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def numeric_leaves(value: Any) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if is_number(child):
                    out.append((str(key), float(child)))
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return out


def gap_leaves(value: Any) -> dict[str, float]:
    """Every ``*gap*`` numeric leaf anywhere under ``value`` (last write wins per key)."""
    out: dict[str, float] = {}
    for key, val in numeric_leaves(value):
        if GAP_KEY_RE.search(key) and key.lower() not in STRUCTURAL_ROW_KEYS:
            out[key] = val
    return out


def infer_layer(name: str) -> str | None:
    match = LAYER_RE.match(name)
    return match.group(1).upper() if match else None


def infer_variant(name: str) -> str:
    for needle, label in VARIANTS:
        if needle in name:
            return label
    return "other"


def approx_equal(a: float, b: float, tol: float = SIG_TOL) -> bool:
    return abs(a - b) <= tol + tol * max(abs(a), abs(b))


# --------------------------------------------------------------------------- claim surface


def _witness_gap_items(data: Any) -> dict[str, float]:
    """Gap leaves from the positive-witness locations (top-level ``positive``, ``controls.positive``,
    ``rows[].layer_gate``), taking the most-favourable (min-abs) value across rungs. A claim that
    is vacuous at its best rung is vacuous."""
    per_key: dict[str, list[float]] = {}
    if not isinstance(data, dict):
        return {}
    sources: list[Any] = []
    if isinstance(data.get("positive"), dict):
        sources.append(data["positive"])
    controls = data.get("controls")
    if isinstance(controls, dict) and isinstance(controls.get("positive"), dict):
        sources.append(controls["positive"])
    for src in sources:
        for key, val in gap_leaves(src).items():
            per_key.setdefault(key, []).append(val)
    rows = data.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                gate = row.get("layer_gate") if isinstance(row.get("layer_gate"), dict) else row
                for key, val in gap_leaves(gate).items():
                    per_key.setdefault(key, []).append(val)
    return {k: min(v, key=abs) for k, v in per_key.items()}


def positive_claim_gaps(data: Any) -> dict[str, float]:
    """Gaps that ARE the layer's positive claim. summary.min_gaps/min_control_gaps are the
    runner's declared claim controls (kept regardless of name); witness-location gaps are
    included only when NOT erasure-named (an erasure leg co-located in a witness block is a
    matched control, not a positive claim)."""
    surface: dict[str, float] = {}
    if not isinstance(data, dict):
        return surface
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    for key in ("min_control_gaps", "min_gaps"):
        gaps = summary.get(key)
        if isinstance(gaps, dict):
            surface.update({k: float(v) for k, v in gaps.items() if is_number(v)})
    for key, val in _witness_gap_items(data).items():
        if not ERASURE_KEY_RE.search(key):
            surface.setdefault(key, val)
    return surface


def erasure_control_gaps(data: Any) -> dict[str, float]:
    """Erasure / equivariance / commuting matched-control gaps (intended-zero by default),
    from witness blocks plus graveyard_companions and controls.negative."""
    surface: dict[str, float] = {k: v for k, v in _witness_gap_items(data).items()
                                 if ERASURE_KEY_RE.search(k)}
    if isinstance(data, dict):
        if isinstance(data.get("graveyard_companions"), dict):
            surface.update(gap_leaves(data["graveyard_companions"]))
        controls = data.get("controls")
        if isinstance(controls, dict) and isinstance(controls.get("negative"), dict):
            surface.update(gap_leaves(controls["negative"]))
    return surface


def required_erasure_patterns(data: Any) -> list[str]:
    """Substrings a receipt declares as load-bearing erasures: if a matching erasure control is
    vacuous, the defining feature did not actually matter -> HARD. This is how a layer (e.g. L2)
    forces its chirality/sheet erasure to bite, without the gate guessing erasure semantics."""
    patterns: list[str] = []
    for _, sub in _walk_dicts(data):
        decl = sub.get("required_load_bearing_erasures")
        if isinstance(decl, list):
            patterns.extend(str(p).lower() for p in decl)
    return patterns


def fenced_control_names(data: Any) -> set[str]:
    names: set[str] = set()
    if not isinstance(data, dict):
        return names
    for key in ("weak_controls_flagged", "weak_diagnostic_controls_flagged"):
        for entry in data.get(key, []) or []:
            if isinstance(entry, dict):
                controls = entry.get("controls")
                if isinstance(controls, dict):
                    names.update(str(n) for n in controls)
                name = entry.get("control") or entry.get("name")
                if isinstance(name, str):
                    names.add(name)
    return names


def claim_baseline_numbers(data: Any) -> list[float]:
    """Claim-bearing baseline values an echoed witness could be copied from, excluding
    bookkeeping counts (NON_SIGNATURE_KEYS / STRUCTURAL_ROW_KEYS). NOT physics-restricted: a
    witness that merely copies an erased-control reading (e.g. peps2d_erased) is a real echo and
    must stay catchable. The witness side IS physics-restricted at the call site, and a recorded
    before/after transition suppresses the flag, so a coincidental count cannot trip it."""
    numbers: list[float] = []
    for src in (data.get("summary"), data.get("controls"), data.get("rows")) if isinstance(data, dict) else ():
        for key, val in numeric_leaves(src):
            if key.lower() in NON_SIGNATURE_KEYS or key.lower() in STRUCTURAL_ROW_KEYS:
                continue
            numbers.append(val)
    return numbers


# --------------------------------------------------------------------------- signatures


def extract_signature(data: Any, variant: str) -> dict[str, float]:
    summary = data.get("summary") if isinstance(data, dict) else None
    summary = summary if isinstance(summary, dict) else {}

    if variant == "full_spinor_network":
        keys = (
            "min_entanglement_gap_vs_product_mps", "min_log_negativity",
            "min_mutual_information", "min_pyg_message_gap",
        )
        sig = {k: float(summary[k]) for k in keys if is_number(summary.get(k))}
        if sig:
            return sig
    if variant == "bond4" and isinstance(summary.get("min_gaps"), dict):
        return {k: float(v) for k, v in summary["min_gaps"].items() if is_number(v)}
    if variant == "depth" and isinstance(summary.get("min_control_gaps"), dict):
        return {k: float(v) for k, v in summary["min_control_gaps"].items() if is_number(v)}

    # Location-agnostic fallback: the claim-physics min over rows[].layer_gate (the l457
    # runner schema). Built from physics keys, NOT bookkeeping counts, so a shared carrier
    # scaffold is comparable across layers instead of separated by per-layer counts.
    rows = data.get("rows") if isinstance(data, dict) else None
    if isinstance(rows, list) and rows:
        per_key: dict[str, list[float]] = {}
        for row in rows:
            if isinstance(row, dict):
                node = row.get("layer_gate") if isinstance(row.get("layer_gate"), dict) else row
                for key, val in numeric_leaves(node):
                    if key.lower() in STRUCTURAL_ROW_KEYS or key.lower() in NON_SIGNATURE_KEYS:
                        continue
                    if ERASURE_KEY_RE.search(key):
                        continue  # intended-zero collapse controls are shared+zero across all layers
                    if PHYSICS_KEY_RE.search(key):
                        per_key.setdefault(key, []).append(val)
        sig = {k: round(min(v, key=abs), 9) for k, v in per_key.items()}
        if sig:
            return sig

    # Last resort: non-bookkeeping, non-erasure numeric leaves of summary (a cross-layer match must
    # rest on real claim physics, not on intended-zero collapse controls shared by every layer).
    sig = {k: v for k, v in numeric_leaves(summary)
           if k.lower() not in NON_SIGNATURE_KEYS and not ERASURE_KEY_RE.search(k)}
    return sig


def signatures_match(a: dict[str, float], b: dict[str, float]) -> bool:
    """Match on the shared key intersection (>= MIN_SIGNATURE_TERMS), so a single renamed
    or omitted key cannot hide a relabelled identical computation."""
    shared = set(a) & set(b)
    if len(shared) < MIN_SIGNATURE_TERMS:
        return False
    return all(approx_equal(a[k], b[k]) for k in shared)


# --------------------------------------------------------------------------- per-file checks


def _ablation_entries(data: Any) -> dict[str, Any]:
    """Union of the ablation record locations across both runner schemas."""
    merged: dict[str, Any] = {}
    if isinstance(data, dict):
        for key in ("tool_ablations", "tool_ablations_by_tool"):
            block = data.get(key)
            if isinstance(block, dict):
                for name, entry in block.items():
                    merged[f"{key}:{name}"] = entry
    return merged


def check_fabricated_ablations(data: Any, layer: str | None, path: Path) -> list[Violation]:
    violations: list[Violation] = []
    if not isinstance(data, dict):
        return violations

    baseline_numbers = claim_baseline_numbers(data)

    # Pattern 2a: ablation_outcome_delta with after-stub hardcoded 0.0 for every tool.
    aod = data.get("ablation_outcome_delta")
    if isinstance(aod, dict) and aod:
        tools = [t for t in aod.values() if isinstance(t, dict)]
        # Skip entries that genuinely recomputed (recomputed=True) or are certificate ablations:
        # their after=0 is a real result, not a stipulation. The stipulation pattern is after=0
        # with NO recompute marker.
        has_after = [
            t for t in tools
            if "control_gap_after_stub" in t
            and not t.get("recomputed") and t.get("ablation_kind") != "certificate"
        ]
        if has_after:
            all_zero = all(abs(float(t.get("control_gap_after_stub", 0.0))) <= SIG_TOL for t in has_after)
            delta_is_before = sum(
                1 for t in has_after
                if is_number(t.get("delta_magnitude")) and is_number(t.get("control_gap_before"))
                and approx_equal(float(t["delta_magnitude"]), float(t["control_gap_before"]))
            )
            if all_zero and delta_is_before >= max(1, len(has_after) - 1):
                violations.append(Violation(
                    "fabricated_ablation_after_zero", "HARD",
                    f"{len(has_after)} tools all set control_gap_after_stub==0.0 with delta==before: "
                    f"the ablation is a stipulation, not a removed-and-re-run measurement",
                    layer, str(path)))

    # Patterns 2b/2c: asserted-no-witness / vacuous-witness / echo, across BOTH ablation blocks.
    asserted: list[str] = []
    vacuous: list[str] = []
    echo: list[str] = []
    cert_invalid: list[str] = []
    after_marker = re.compile(r"(after|ablated|removal)", re.IGNORECASE)
    for name, entry in _ablation_entries(data).items():
        if not isinstance(entry, dict):
            continue
        # Certificate ablations: a tool issuing a structural proof/topology/geometry certificate.
        # Honest iff the certificate is issued WITH the tool, absent WITHOUT it, and carries a
        # numeric certified value. They are not numeric gap collapses, so the numeric checks below
        # do not apply.
        if entry.get("ablation_kind") == "certificate":
            if entry.get("pass") is True or entry.get("non_vacuous") is True:
                valid = (
                    entry.get("provable_with_tool") is True
                    and entry.get("provable_without_tool") is False
                    and is_number(entry.get("certificate_value"))
                )
                if not valid:
                    cert_invalid.append(name)
            continue
        witness = entry.get("delta_witness")
        witness_dict = witness if isinstance(witness, dict) else {}
        # The entry claims to be a real ablation if it (or its witness) asserts so.
        claims_real = (
            entry.get("non_vacuous") is True or entry.get("pass") is True
            or witness_dict.get("non_vacuous") is True or witness_dict.get("pass") is True
        )
        if not claims_real:
            continue
        witness_numbers = [v for _, v in numeric_leaves(witness)] if witness is not None else []
        witness_gaps = list(gap_leaves(witness).values()) if witness is not None else []
        # Echo compares only claim-physics witness numbers against claim-physics baselines.
        witness_physics = [v for k, v in numeric_leaves(witness) if PHYSICS_KEY_RE.search(k)] if witness is not None else []
        # A recorded before/after transition (any after-named field, or the baseline/ablated
        # boolean pair) proves the ablation actually re-ran -> not an echo.
        has_after = (
            any(after_marker.search(str(k)) for k in entry)
            or any(after_marker.search(str(k)) for k in witness_dict)
            or ("baseline_pass" in entry and "ablated_pass" in entry)
        )
        if not witness_numbers:
            asserted.append(name)
        elif witness_gaps and all(abs(g) < GAP_FLOOR for g in witness_gaps):
            vacuous.append(name)            # asserts non_vacuous but every witness gap is ~0
        elif not has_after and any(
            approx_equal(wn, bn) for wn in witness_physics for bn in baseline_numbers
        ):
            echo.append(name)               # witness merely copies a with-tool baseline value

    if asserted:
        violations.append(Violation(
            "asserted_ablation_no_witness", "HARD",
            f"ablations {sorted(asserted)} assert non_vacuous/pass with no numeric delta_witness",
            layer, str(path)))
    if vacuous:
        violations.append(Violation(
            "vacuous_ablation_witness", "HARD",
            f"ablations {sorted(vacuous)} assert non_vacuous but every witness gap is below "
            f"GAP_FLOOR={GAP_FLOOR:g} -- the witness cannot fail",
            layer, str(path)))
    if echo:
        violations.append(Violation(
            "delta_witness_echoes_baseline", "HARD",
            f"ablations {sorted(echo)} have a witness equal to a claim-bearing baseline with no "
            f"after-removal value -- it is the with-tool reading, not an after-removal delta",
            layer, str(path)))
    if cert_invalid:
        violations.append(Violation(
            "certificate_ablation_invalid", "HARD",
            f"certificate ablations {sorted(cert_invalid)} claim load-bearing but lack a genuine "
            f"provability flip (provable_with_tool=True, provable_without_tool=False) with a numeric "
            f"certificate_value -- a certificate that is not actually issued-and-required is theater",
            layer, str(path)))
    return violations


def check_controls(data: Any, layer: str | None, path: Path) -> list[Violation]:
    violations: list[Violation] = []
    claim = positive_claim_gaps(data)
    erasure = erasure_control_gaps(data)
    fenced = fenced_control_names(data)
    required = required_erasure_patterns(data)

    if not claim and not erasure and not extract_signature(data, "other"):
        # Nothing observable at all -> absence is not a pass.
        violations.append(Violation(
            "no_observable_signature", "HARD",
            "receipt exposes no claim-bearing gap or signature anywhere "
            "(summary/positive/controls.positive/rows.layer_gate all empty) -- not auditable, not a pass",
            layer, str(path)))
        return violations

    # Vacuous positive/claim controls (HARD unless honestly fenced).
    for name, value in claim.items():
        if abs(value) < GAP_FLOOR:
            if name in fenced:
                violations.append(Violation(
                    "vacuous_control_fenced", "SOFT",
                    f"claim control '{name}'={value:.3e} below GAP_FLOOR but fenced as diagnostic",
                    layer, str(path)))
            else:
                violations.append(Violation(
                    "vacuous_claim_bearing_control", "HARD",
                    f"positive/claim control '{name}'={value:.3e} below GAP_FLOOR={GAP_FLOOR:g} "
                    f"and not fenced -- a claim with no signal that cannot fail",
                    layer, str(path)))

    # Erasure / matched controls: intended-zero by default (SOFT), UNLESS the receipt declares
    # the erasure load-bearing -- then a vacuous erasure means the defining feature did not matter.
    for name, value in erasure.items():
        if abs(value) < GAP_FLOOR:
            if any(pat in name.lower() for pat in required):
                violations.append(Violation(
                    "vacuous_required_erasure", "HARD",
                    f"declared load-bearing erasure '{name}'={value:.3e} is below GAP_FLOOR "
                    f"-- erasing the defining structure changed nothing, so it is not load-bearing",
                    layer, str(path)))
            else:
                violations.append(Violation(
                    "vacuous_erasure_control", "SOFT",
                    f"erasure/matched control '{name}'={value:.3e} below GAP_FLOOR "
                    f"(intended collapse unless this erasure is meant to be load-bearing; "
                    f"declare it in required_load_bearing_erasures to make this HARD)",
                    layer, str(path)))

    # Collapsed controls: distinct names sharing one value.
    items = [(n, v) for n, v in claim.items() if abs(v) >= GAP_FLOOR]
    collapsed = False
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if approx_equal(items[i][1], items[j][1]):
                collapsed = True
                violations.append(Violation(
                    "collapsed_controls", "SOFT",
                    f"controls '{items[i][0]}' and '{items[j][0]}' collapse to {items[i][1]:.6g} "
                    f"-- likely the same operation under two names",
                    layer, str(path)))

    # Too few distinct real controls -> "fence everything" dodge.
    distinct: list[float] = []
    for _, value in items:
        if not any(approx_equal(value, seen) for seen in distinct):
            distinct.append(value)
    if len(distinct) < MIN_NONVACUOUS_CONTROLS and not collapsed:
        violations.append(Violation(
            "insufficient_nonvacuous_controls", "HARD",
            f"only {len(distinct)} distinct non-vacuous claim controls (need >= "
            f"{MIN_NONVACUOUS_CONTROLS}); a layer cannot survive by fencing its real controls",
            layer, str(path)))
    return violations


def iter_rows_lists(value: Any) -> Iterable[list]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "rows" and isinstance(child, list) and len(child) >= 2 \
                    and all(isinstance(r, dict) for r in child):
                yield child
            else:
                yield from iter_rows_lists(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_rows_lists(child)


def row_size(row: dict) -> Any:
    for key in ("site_count", "sites", "max_sites", "qubits", "shape", "n"):
        if key in row:
            return json.dumps(row[key], sort_keys=True)
    return None


def declared_invariant_keys(data: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(data, dict):
        for _, sub in _walk_dicts(data):
            decl = sub.get("expected_N_invariant")
            if isinstance(decl, list):
                names.update(str(n) for n in decl)
    return names


def _walk_dicts(value: Any) -> Iterable[tuple[str, dict]]:
    if isinstance(value, dict):
        yield "", value
        for k, v in value.items():
            yield from _walk_dicts(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_dicts(v)


def check_scale_ladder(data: Any, layer: str | None, path: Path) -> list[Violation]:
    violations: list[Violation] = []
    declared = declared_invariant_keys(data)
    for rows in iter_rows_lists(data):
        sizes = {row_size(r) for r in rows}
        sizes.discard(None)
        if len(sizes) < 2:
            continue
        # Per-key physics across rungs (descend into layer_gate where present).
        per_key: dict[str, list[float]] = {}
        for r in rows:
            node = r.get("layer_gate") if isinstance(r.get("layer_gate"), dict) else r
            for key, val in numeric_leaves(node):
                if key.lower() in STRUCTURAL_ROW_KEYS or key.lower() in NON_SIGNATURE_KEYS:
                    continue
                if ERASURE_KEY_RE.search(key):
                    continue  # erasure/matched controls are intended-zero at every N; check_controls handles them
                if PHYSICS_KEY_RE.search(key):
                    per_key.setdefault(key, []).append(round(val, 9))
        for key, vals in per_key.items():
            if len(vals) < 2:
                continue
            if all(approx_equal(v, vals[0]) for v in vals):
                if INVARIANT_KEY_RE.search(key) or key in declared:
                    violations.append(Violation(
                        "declared_invariant_scale", "SOFT",
                        f"claim key '{key}'={vals[0]:.6g} is N-invariant across {len(sizes)} rungs "
                        f"and declared/named invariant -- allowed but verify the invariance is earned",
                        layer, str(path)))
                else:
                    violations.append(Violation(
                        "vacuous_scale_ladder", "HARD",
                        f"claim key '{key}'={vals[0]:.6g} is identical across {len(sizes)} distinct "
                        f"site counts -- the 64-site rung adds no information over the 8-site rung "
                        f"(declare expected_N_invariant if this is a genuine topological invariant)",
                        layer, str(path)))
    return violations


# --------------------------------------------------------------------------- corpus checks


def check_cross_layer(receipts: list[Receipt]) -> list[Violation]:
    violations: list[Violation] = []
    by_variant: dict[str, list[Receipt]] = {}
    for r in receipts:
        if r.layer and len(r.signature) >= MIN_SIGNATURE_TERMS:
            by_variant.setdefault(r.variant, []).append(r)
    for variant, group in by_variant.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a.layer == b.layer or not signatures_match(a.signature, b.signature):
                    continue
                shared = sorted(set(a.signature) & set(b.signature))
                sample = ", ".join(f"{k}={a.signature[k]:.6g}" for k in shared[:3])
                violations.append(Violation(
                    "cross_layer_signature_identity", "HARD",
                    f"{a.layer} and {b.layer} emit an identical {variant} signature [{sample}] "
                    f"-- nominally distinct layers are the same computation relabelled",
                    layer=f"{a.layer}/{b.layer}", path=f"{a.path.name} == {b.path.name}"))
    return violations


def check_shared_constant(receipts: list[Receipt]) -> list[Violation]:
    near_ln8 = [
        r for r in receipts
        if r.variant == "full_spinor_network"
        and is_number(r.signature.get("min_entanglement_gap_vs_product_mps"))
        and abs(r.signature["min_entanglement_gap_vs_product_mps"] - LN8) < 1e-3
    ]
    if len(near_ln8) >= 3:
        layers = sorted({r.layer for r in near_ln8 if r.layer})
        return [Violation(
            "shared_dimension_constant", "SOFT",
            f"min_entanglement_gap_vs_product_mps == ln(8)={LN8:.5f} (saturated, dimension-only) "
            f"across {layers} -- this signature term carries zero per-layer information")]
    return []


# --------------------------------------------------------------------------- driver


def gather_receipts(paths: list[Path]) -> list[Receipt]:
    receipts: list[Receipt] = []
    for path in paths:
        data = load_json(path)
        variant = infer_variant(path.name)
        receipt = Receipt(path=path, layer=infer_layer(path.name), variant=variant, data=data)
        receipt.signature = extract_signature(data, variant)
        receipts.append(receipt)
    return receipts


def has_observable_surface(receipt: Receipt) -> bool:
    return (
        len(receipt.signature) >= MIN_SIGNATURE_TERMS
        or bool(positive_claim_gaps(receipt.data))
        or bool(erasure_control_gaps(receipt.data))
    )


def evaluate(paths: list[Path]) -> dict[str, Any]:
    receipts = gather_receipts(paths)
    violations: list[Violation] = []
    for r in receipts:
        violations += check_fabricated_ablations(r.data, r.layer, r.path)
        violations += check_controls(r.data, r.layer, r.path)
        violations += check_scale_ladder(r.data, r.layer, r.path)
    violations += check_cross_layer(receipts)
    violations += check_shared_constant(receipts)

    hard = [v for v in violations if v.severity == "HARD"]
    soft = [v for v in violations if v.severity == "SOFT"]

    scoreboard: dict[str, dict[str, Any]] = {}
    for r in receipts:
        key = r.layer or "unknown"
        entry = scoreboard.setdefault(key, {"hard": 0, "soft": 0, "receipts": 0,
                                            "observable_surface": 0, "codes": []})
        entry["receipts"] += 1
        if has_observable_surface(r):
            entry["observable_surface"] += 1
    for v in violations:
        for key in (v.layer or "unknown").split("/"):
            entry = scoreboard.setdefault(key, {"hard": 0, "soft": 0, "receipts": 0,
                                                "observable_surface": 0, "codes": []})
            entry["hard" if v.severity == "HARD" else "soft"] += 1
            entry["codes"].append(v.code)
    for entry in scoreboard.values():
        entry["passes_distinctness_gate"] = entry["hard"] == 0 and entry["observable_surface"] > 0
        # A layer with no HARD flags but little observable surface is UNKNOWN, not clean.
        entry["rankable"] = entry["observable_surface"] >= max(1, entry["receipts"] - 1)

    return {
        "ok": not hard,
        "receipts_checked": len(receipts),
        "hard_violations": len(hard),
        "soft_violations": len(soft),
        "scoreboard": dict(sorted(scoreboard.items())),
        "violations": [vars(v) for v in violations],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="result JSON files (default: all layer receipts)")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--report-only", action="store_true", help="exit 0 even with HARD violations")
    parser.add_argument("--scoreboard", action="store_true", help="print only the per-layer scoreboard")
    args = parser.parse_args(argv)

    if args.paths:
        paths = [p for p in args.paths if p.exists()]
    else:
        paths = sorted(p for p in args.results_dir.glob("[lr]*_*_results.json") if LAYER_RE.match(p.name))

    if not paths:
        print(json.dumps({"ok": False, "error": "no layer result receipts found"}, indent=2))
        return 1

    report = evaluate(paths)
    print(json.dumps(report["scoreboard"] if args.scoreboard else report, indent=2, sort_keys=True))
    return 0 if (report["ok"] or args.report_only) else 1


if __name__ == "__main__":
    raise SystemExit(main())
