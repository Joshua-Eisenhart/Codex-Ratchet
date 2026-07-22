"""Bounded N=3 whole-state Ratchet simulation.

This module deliberately stays below a physics claim.  It executes a finite
comparison campaign on one three-qubit carrier S,E1,E2.  Every candidate is a
whole density operator plus an explicit nesting diagram.  Ordered engine
channels, a postselected coherent-history control, marginal consistency,
finite extension fibres, instruments, SBS diagnostics, topological boundary
compatibility, typed telemetry and Pareto comparison are all kept distinct.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from itertools import combinations
from math import log
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np


Array = np.ndarray
TOL = 1.0e-10

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
P0 = np.array([[1, 0], [0, 0]], dtype=complex)
P1 = np.array([[0, 0], [0, 1]], dtype=complex)


def dagger(a: Array) -> Array:
    return np.asarray(a).conj().T


def hermitize(a: Array) -> Array:
    return (np.asarray(a) + dagger(a)) / 2.0


def kron_all(items: Sequence[Array]) -> Array:
    out = np.array([[1.0 + 0.0j]])
    for item in items:
        out = np.kron(out, item)
    return out


def embed_one(op: Array, target: int, n: int = 3) -> Array:
    return kron_all([op if i == target else I2 for i in range(n)])


def unitary(axis: Array, angle: float) -> Array:
    return np.cos(angle / 2.0) * I2 - 1j * np.sin(angle / 2.0) * axis


def trace_norm_hermitian(a: Array) -> float:
    return float(np.sum(np.abs(np.linalg.eigvalsh(hermitize(a)))))


def trace_distance(a: Array, b: Array) -> float:
    return 0.5 * trace_norm_hermitian(a - b)


def entropy_vn(rho: Array, base: float = np.e) -> float:
    vals = np.linalg.eigvalsh(hermitize(rho))
    vals = np.clip(vals.real, 0.0, None)
    vals = vals[vals > 1.0e-15]
    if not vals.size:
        return 0.0
    return float(-np.sum(vals * np.log(vals)) / np.log(base))


def relative_entropy(rho: Array, sigma: Array) -> float:
    """Umegaki D(rho||sigma), with +inf on support failure."""

    rho = hermitize(rho)
    sigma = hermitize(sigma)
    er, vr = np.linalg.eigh(rho)
    es, vs = np.linalg.eigh(sigma)
    er = np.clip(er.real, 0.0, None)
    es = np.clip(es.real, 0.0, None)
    log_r = np.zeros_like(er)
    nz_r = er > 1.0e-15
    log_r[nz_r] = np.log(er[nz_r])
    support_s = vs[:, es > 1.0e-15]
    if support_s.shape[1] < sigma.shape[0]:
        kernel = vs[:, es <= 1.0e-15]
        leaked = float(np.trace(dagger(kernel) @ rho @ kernel).real)
        if leaked > 1.0e-12:
            return float("inf")
    log_s_matrix = (
        support_s
        @ np.diag(np.log(es[es > 1.0e-15]))
        @ dagger(support_s)
    )
    log_r_matrix = vr @ np.diag(log_r) @ dagger(vr)
    return float(np.trace(rho @ (log_r_matrix - log_s_matrix)).real)


def sqrt_psd(a: Array) -> Array:
    vals, vecs = np.linalg.eigh(hermitize(a))
    vals = np.clip(vals.real, 0.0, None)
    return vecs @ np.diag(np.sqrt(vals)) @ dagger(vecs)


def root_fidelity(rho: Array, sigma: Array) -> float:
    sr = sqrt_psd(rho)
    inside = sr @ sigma @ sr
    return float(np.clip(np.trace(sqrt_psd(inside)).real, 0.0, 1.0))


def partial_trace(rho: Array, keep: Sequence[int], dims: Sequence[int] = (2, 2, 2)) -> Array:
    """Trace out all factors not in ``keep``; retained factors keep input order."""

    keep_tuple = tuple(keep)
    if tuple(sorted(keep_tuple)) != keep_tuple:
        raise ValueError("keep must be in ascending subsystem order")
    n = len(dims)
    arr = np.asarray(rho, dtype=complex).reshape(tuple(dims) + tuple(dims))
    live_dims = list(dims)
    for axis in sorted(set(range(n)) - set(keep_tuple), reverse=True):
        arr = np.trace(arr, axis1=axis, axis2=axis + len(live_dims))
        live_dims.pop(axis)
    d = int(np.prod(live_dims, dtype=int)) if live_dims else 1
    return hermitize(arr.reshape((d, d)))


def apply_kraus(rho: Array, kraus: Sequence[Array]) -> Array:
    out = sum((k @ rho @ dagger(k) for k in kraus), np.zeros_like(rho))
    return hermitize(out)


def apply_local_kraus(rho: Array, kraus: Sequence[Array], target: int) -> Array:
    return apply_kraus(rho, [embed_one(k, target) for k in kraus])


def dephase_kraus(axis: Array, strength: float) -> tuple[Array, Array]:
    p = float(np.clip(strength, 0.0, 1.0))
    return np.sqrt(1.0 - p) * I2, np.sqrt(p) * axis


def depolarizing_kraus(strength: float) -> tuple[Array, Array, Array, Array]:
    p = float(np.clip(strength, 0.0, 1.0))
    return (
        np.sqrt(1.0 - 3.0 * p / 4.0) * I2,
        np.sqrt(p / 4.0) * X,
        np.sqrt(p / 4.0) * Y,
        np.sqrt(p / 4.0) * Z,
    )


def terrain_kraus(terrain: str, strength: float, chirality: int) -> tuple[Array, ...]:
    """Finite scratch terrain channels; every returned map is unital CPTP."""

    if terrain == "Se":
        return depolarizing_kraus(0.05 + 0.30 * strength)
    if terrain == "Ne":
        return (unitary(Y, chirality * (0.05 + 0.35 * strength)),)
    if terrain == "Ni":
        return dephase_kraus(Z, 0.10 + 0.35 * strength)
    if terrain == "Si":
        return dephase_kraus(X, 0.06 + 0.25 * strength)
    raise KeyError(terrain)


def operator_kraus(name: str, angle: float, chirality: int) -> tuple[Array, ...]:
    if name == "Dz":
        return dephase_kraus(Z, 0.08 + 0.10 * angle)
    if name == "Dx":
        return dephase_kraus(X, 0.08 + 0.10 * angle)
    if name == "Ux":
        return (unitary(X, chirality * angle),)
    if name == "Uz":
        return (unitary(Z, chirality * angle),)
    raise KeyError(name)


@dataclass(frozen=True)
class Stage:
    index: int
    engine: int
    loop: str
    position: int
    terrain: str
    target: int
    chirality: int
    native_operator: str
    terrain_first: bool
    strength: float
    angle: float

    @property
    def stage_id(self) -> str:
        return f"E{self.engine}:{self.loop}:{self.position}:{self.terrain}:{self.native_operator}"


def build_stages() -> list[Stage]:
    """The complete two-engine chart: 8 stages per type, 16 total."""

    chart = [
        # Engine 1: outer deductive, inner inductive.
        (1, "outer", ("Se", "Ne", "Ni", "Si"), ("Dz", "Dz", "Uz", "Uz"), (True, False, True, False)),
        (1, "inner", ("Se", "Si", "Ni", "Ne"), ("Ux", "Dx", "Dx", "Ux"), (False, True, False, True)),
        # Engine 2: outer inductive, inner deductive.
        (2, "outer", ("Se", "Si", "Ni", "Ne"), ("Ux", "Dx", "Dx", "Ux"), (True, False, True, False)),
        (2, "inner", ("Se", "Ne", "Ni", "Si"), ("Dz", "Dz", "Uz", "Uz"), (False, True, False, True)),
    ]
    stages: list[Stage] = []
    idx = 0
    for engine, loop_name, terrains, native_ops, orders in chart:
        for position, (terrain, native_op, terrain_first) in enumerate(
            zip(terrains, native_ops, orders), start=1
        ):
            # Each engine couples its own fragment to the shared system.
            fragment = 1 if engine == 1 else 2
            target = 0 if position % 2 else fragment
            stages.append(
                Stage(
                    index=idx,
                    engine=engine,
                    loop=loop_name,
                    position=position,
                    terrain=terrain,
                    target=target,
                    chirality=1 if engine == 1 else -1,
                    native_operator=native_op,
                    terrain_first=terrain_first,
                    strength=0.22 + 0.025 * idx,
                    angle=0.13 + 0.011 * idx,
                )
            )
            idx += 1
    return stages


OPERATORS = ("Dz", "Dx", "Ux", "Uz")


def apply_stage_map(rho: Array, stage: Stage, operator: str) -> Array:
    terrain = terrain_kraus(stage.terrain, stage.strength, stage.chirality)
    intrinsic = operator_kraus(operator, stage.angle, stage.chirality)
    if stage.terrain_first:
        return apply_local_kraus(apply_local_kraus(rho, terrain, stage.target), intrinsic, stage.target)
    return apply_local_kraus(apply_local_kraus(rho, intrinsic, stage.target), terrain, stage.target)


def z_instrument() -> dict[int, Array]:
    return {0: embed_one(P0, 0), 1: embed_one(P1, 0)}


def instrument_records(rho: Array, instrument: Mapping[int, Array] | None = None) -> dict[str, Any]:
    instrument = instrument or z_instrument()
    completeness = sum((dagger(k) @ k for k in instrument.values()), np.zeros_like(rho))
    records: dict[str, Any] = {}
    for outcome, k in instrument.items():
        post = hermitize(k @ rho @ dagger(k))
        probability = float(np.trace(post).real)
        records[str(outcome)] = {
            "probability": probability,
            "conditional_state": post / probability if probability > 1.0e-15 else post,
        }
    return {
        "records": records,
        "probability_sum": float(sum(v["probability"] for v in records.values())),
        "completeness_error": float(np.linalg.norm(completeness - np.eye(rho.shape[0]))),
    }


def conditional_fragment_states(rho: Array, fragment: int) -> tuple[list[float], list[Array]]:
    inst = instrument_records(rho)
    priors: list[float] = []
    states: list[Array] = []
    for z in ("0", "1"):
        priors.append(float(inst["records"][z]["probability"]))
        states.append(partial_trace(inst["records"][z]["conditional_state"], (fragment,)))
    return priors, states


def dephase_system(rho: Array) -> Array:
    return apply_kraus(rho, tuple(z_instrument().values()))


def cmi_e1_e2_given_s(rho: Array) -> float:
    # I(E1:E2|S) = S(SE1)+S(SE2)-S(S)-S(SE1E2).
    return float(
        entropy_vn(partial_trace(rho, (0, 1)))
        + entropy_vn(partial_trace(rho, (0, 2)))
        - entropy_vn(partial_trace(rho, (0,)))
        - entropy_vn(rho)
    )


def sbs_diagnostics(rho: Array) -> dict[str, Any]:
    fragment_rows: list[dict[str, float]] = []
    for fragment in (1, 2):
        priors, states = conditional_fragment_states(rho, fragment)
        weighted_delta = priors[0] * states[0] - priors[1] * states[1]
        p_guess = 0.5 * (1.0 + trace_norm_hermitian(weighted_delta))
        fragment_rows.append(
            {
                "fragment": float(fragment),
                "root_fidelity": root_fidelity(states[0], states[1]),
                "helstrom_guessing_probability": float(p_guess),
                "prior_0": priors[0],
                "prior_1": priors[1],
            }
        )
    return {
        "system_dephasing_trace_distance": trace_distance(rho, dephase_system(rho)),
        "fragment_records": fragment_rows,
        "max_fragment_root_fidelity": max(r["root_fidelity"] for r in fragment_rows),
        "min_fragment_guessing_probability": min(
            r["helstrom_guessing_probability"] for r in fragment_rows
        ),
        "conditional_mutual_information_E1_E2_given_S": cmi_e1_e2_given_s(rho),
    }


def erase_fragment_records(rho: Array, fragments: Sequence[int] = (1, 2)) -> Array:
    """Apply a completely depolarising channel to selected record fragments."""

    out = rho
    for fragment in fragments:
        out = apply_local_kraus(out, depolarizing_kraus(1.0), fragment)
    return out


def sbs_falsification_controls(rho: Array) -> dict[str, Any]:
    """Preregistered controls that must move SBS diagnostics predictably.

    These are diagnostics of record structure, not an assertion that SBS is a
    necessary ontological definition of an object.
    """

    baseline = sbs_diagnostics(rho)

    # Destroy both environmental records. The fragments should become
    # indistinguishable and binary guessing should fall to chance.
    erased_state = erase_fragment_records(rho, (1, 2))
    erased = sbs_diagnostics(erased_state)
    prior_only_guessing = max(
        erased["fragment_records"][0]["prior_0"],
        erased["fragment_records"][0]["prior_1"],
    )

    # Destroy only E2. This is a false/single-fragment broadcast: E1 still has
    # a record, but redundancy across both fragments has failed.
    single_fragment_state = erase_fragment_records(rho, (2,))
    single_fragment = sbs_diagnostics(single_fragment_state)
    fragment_guesses = [
        row["helstrom_guessing_probability"]
        for row in single_fragment["fragment_records"]
    ]

    # Remove only the off-diagonal pointer phase. This must drive the system
    # dephasing residual to zero without being confused with record erasure.
    phase_scrambled_state = dephase_system(rho)
    phase_scrambled = sbs_diagnostics(phase_scrambled_state)

    checks = {
        "record_erasure_lowers_min_guessing": (
            erased["min_fragment_guessing_probability"]
            < baseline["min_fragment_guessing_probability"] - 0.25
        ),
        "record_erasure_raises_fragment_fidelity": (
            erased["max_fragment_root_fidelity"]
            > baseline["max_fragment_root_fidelity"] + 0.25
        ),
        "record_erasure_reaches_prior_only_guessing_within_1e-10": abs(
            erased["min_fragment_guessing_probability"] - prior_only_guessing
        ) < 1.0e-10,
        "single_fragment_control_breaks_redundancy": (
            max(fragment_guesses) - min(fragment_guesses) > 0.25
            and single_fragment["min_fragment_guessing_probability"]
            < baseline["min_fragment_guessing_probability"] - 0.25
        ),
        "phase_scramble_reduces_coherence_residual": (
            phase_scrambled["system_dephasing_trace_distance"]
            < baseline["system_dephasing_trace_distance"] - 0.05
        ),
        "phase_scramble_residual_zero_within_1e-10": (
            phase_scrambled["system_dephasing_trace_distance"] < 1.0e-10
        ),
    }
    return {
        "baseline": baseline,
        "record_erasure_both_fragments": erased,
        "prior_only_guessing_probability": prior_only_guessing,
        "false_broadcast_single_fragment_E1_only": single_fragment,
        "single_fragment_guessing_probabilities": fragment_guesses,
        "phase_scramble_system_pointer_basis": phase_scrambled,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def same_boundary_different_bulk_control(tolerance: float = 1.0e-8) -> dict[str, Any]:
    """Show that a boundary-only compression can discard an interior phase.

    GHZ+ and GHZ- have identical one- and two-qubit marginals, and are assigned
    the same finite boundary cochain, yet the interior-sensitive XXX probe gives
    opposite values. Thus the boundary representation is sufficient only for a
    declared probe family; it cannot stand in for unrestricted bulk geometry.
    """

    ket000 = np.zeros(8, dtype=complex)
    ket111 = np.zeros(8, dtype=complex)
    ket000[0] = 1.0
    ket111[7] = 1.0
    plus = (ket000 + ket111) / np.sqrt(2.0)
    minus = (ket000 - ket111) / np.sqrt(2.0)
    rho_plus = np.outer(plus, plus.conj())
    rho_minus = np.outer(minus, minus.conj())

    boundary_plus = derived_marginals(rho_plus)
    boundary_minus = derived_marginals(rho_minus)
    boundary_errors = {
        cut: trace_distance(boundary_plus[cut], boundary_minus[cut])
        for cut in CUTS
    }
    interior_probe = kron_all((X, X, X))
    expectation_plus = float(np.trace(rho_plus @ interior_probe).real)
    expectation_minus = float(np.trace(rho_minus @ interior_probe).real)
    epsilon_pi = abs(expectation_plus - expectation_minus)
    shared_cochain = {"0-1": 1, "1-2": 1, "0-2": 2, "modulus": 5}
    return {
        "states": ["GHZ_plus", "GHZ_minus"],
        "compressed_boundary_data": {
            "proper_marginal_trace_distances": boundary_errors,
            "maximum_proper_marginal_trace_distance": max(boundary_errors.values()),
            "shared_Z5_cochain": shared_cochain,
        },
        "interior_sensitive_probe": "X tensor X tensor X",
        "probe_expectation_GHZ_plus": expectation_plus,
        "probe_expectation_GHZ_minus": expectation_minus,
        "epsilon_Pi": epsilon_pi,
        "tolerance": tolerance,
        "boundary_indistinguishable": max(boundary_errors.values()) <= tolerance,
        "interior_probe_distinguishes": epsilon_pi > tolerance,
        "compression_sufficient_for_interior_probe": False,
        "claim": (
            "Same cochain and proper marginals do not determine the three-body phase; "
            "boundary compression must name and test its licensed probe family."
        ),
    }


def candidate_selection_key(rho: Array, prior: Array) -> tuple[float, float, float]:
    """Explicit demand-specific heuristic for H_select, not an MSS theorem."""

    sbs = sbs_diagnostics(rho)
    return (
        sbs["min_fragment_guessing_probability"],
        -sbs["system_dephasing_trace_distance"],
        -trace_distance(prior, rho),
    )


def stage_transform(
    rho: Array,
    stage: Stage,
    hypothesis: str,
    selected_operator: str | None = None,
) -> tuple[Array, str | tuple[str, ...]]:
    if hypothesis == "H_native":
        return apply_stage_map(rho, stage, stage.native_operator), stage.native_operator
    if hypothesis == "H_select":
        if selected_operator is None:
            trials = [(op, apply_stage_map(rho, stage, op)) for op in OPERATORS]
            selected_operator, selected_state = max(
                trials, key=lambda item: candidate_selection_key(item[1], rho)
            )
            return selected_state, selected_operator
        return apply_stage_map(rho, stage, selected_operator), selected_operator
    if hypothesis == "H_all4":
        out = rho
        for op in OPERATORS:
            out = apply_stage_map(out, stage, op)
        return out, OPERATORS
    if hypothesis == "H_mix":
        outputs = [apply_stage_map(rho, stage, op) for op in OPERATORS]
        return hermitize(sum(outputs) / len(outputs)), OPERATORS
    raise KeyError(hypothesis)


def run_ordered_hypothesis(
    initial: Array,
    hypothesis: str,
    stages: Sequence[Stage],
    skip_indices: Iterable[int] = (),
    reverse: bool = False,
) -> dict[str, Any]:
    """Execute one ordered engine hypothesis and retain every stage receipt."""

    skip = set(skip_indices)
    order = list(reversed(stages)) if reverse else list(stages)
    rho = initial.copy()
    sigma = 0.80 * np.eye(8) / 8.0 + 0.20 * initial
    tau = np.eye(8) / 8.0
    stage_receipts: list[dict[str, Any]] = []
    for stage in order:
        if stage.index in skip:
            continue
        before = rho
        before_sigma = sigma
        before_tau = tau
        rho, selected = stage_transform(before, stage, hypothesis)
        # Use the same realised map on references. H_select is licensed only
        # conditionally on the selected operator; its policy as a whole is adaptive.
        sigma, _ = stage_transform(before_sigma, stage, hypothesis, selected if isinstance(selected, str) else None)
        tau, _ = stage_transform(before_tau, stage, hypothesis, selected if isinstance(selected, str) else None)
        d_before = relative_entropy(before, np.eye(8) / 8.0)
        d_after = relative_entropy(rho, np.eye(8) / 8.0)
        dpi_before = relative_entropy(before, before_sigma)
        dpi_after = relative_entropy(rho, sigma)
        inst = instrument_records(rho)
        stage_receipts.append(
            {
                "stage_id": stage.stage_id,
                "stage_index": stage.index,
                "engine": stage.engine,
                "loop": stage.loop,
                "terrain": stage.terrain,
                "target": stage.target,
                "selected_operator": selected,
                "trace_displacement": trace_distance(before, rho),
                "spohn_discrete": d_before - d_after,
                "invariant_reference_error": trace_distance(tau, np.eye(8) / 8.0),
                "dpi_drop": dpi_before - dpi_after,
                "record_distribution": {
                    key: value["probability"] for key, value in inst["records"].items()
                },
                "instrument_completeness_error": inst["completeness_error"],
                "output_von_neumann_entropy": entropy_vn(rho),
            }
        )
    return {
        "hypothesis": hypothesis,
        "rho": rho,
        "stage_receipts": stage_receipts,
        "spohn_sum": float(sum(r["spohn_discrete"] for r in stage_receipts)),
        "dpi_sum": float(sum(r["dpi_drop"] for r in stage_receipts)),
        "minimum_spohn": float(min((r["spohn_discrete"] for r in stage_receipts), default=0.0)),
        "minimum_dpi_drop": float(min((r["dpi_drop"] for r in stage_receipts), default=0.0)),
        "all_invariant_reference_errors": [r["invariant_reference_error"] for r in stage_receipts],
        "adaptive_policy": hypothesis == "H_select",
    }


def run_coherent_history(initial: Array, stages: Sequence[Stage]) -> dict[str, Any]:
    """A distinct postselected coherent-history candidate.

    At every stage, two unitary branch Kraus amplitudes Ux/sqrt(2) and
    Uz/sqrt(2) are coherently erased onto the same record outcome.  The class
    operator factorises the 2^16 path sum.  Conditioning on that record is not
    a trace-preserving channel, so Spohn telemetry is deliberately unlicensed.
    """

    class_operator = np.eye(8, dtype=complex)
    for stage in stages:
        ux = embed_one(unitary(X, stage.chirality * stage.angle), stage.target)
        uz = embed_one(unitary(Z, stage.chirality * stage.angle), stage.target)
        erased_branch = (ux + np.exp(1j * 0.07 * (stage.index + 1)) * uz) / 2.0
        class_operator = erased_branch @ class_operator
    unnormalized = class_operator @ initial @ dagger(class_operator)
    success_probability = float(np.trace(unnormalized).real)
    if success_probability <= 1.0e-15:
        raise RuntimeError("coherent-history postselection has zero support")
    rho = hermitize(unnormalized / success_probability)
    return {
        "hypothesis": "H_coherent_history",
        "rho": rho,
        "path_count_factorized": 2 ** len(stages),
        "postselection_success_probability": success_probability,
        "trace_preserving": False,
        "spohn_status": "UNLICENSED_POSTSELECTED_NON_TP",
        "ordered_channel_replacement": False,
    }


def make_initial_state(coherence: float = 0.18, noise: float = 0.015) -> Array:
    """Noisy, partially coherent broadcast seed on S,E1,E2."""

    p0 = 0.57
    ket0 = np.zeros(8, dtype=complex)
    ket1 = np.zeros(8, dtype=complex)
    ket0[0] = 1.0
    ket1[7] = 1.0
    broadcast = p0 * np.outer(ket0, ket0.conj()) + (1 - p0) * np.outer(ket1, ket1.conj())
    coherent = np.sqrt(p0 * (1 - p0)) * (
        np.outer(ket0, ket1.conj()) + np.outer(ket1, ket0.conj())
    )
    rho = broadcast + coherence * coherent
    rho = (1.0 - noise) * rho + noise * np.eye(8) / 8.0
    return hermitize(rho / np.trace(rho))


@dataclass(frozen=True)
class Diagram:
    diagram_id: str
    edges: tuple[tuple[int, int], ...]
    modulus: int
    cochain: Mapping[tuple[int, int], int]
    parent_diagram: str | None = None
    structural_charge: int = 0

    def obstruction(self) -> int:
        triangle = {(0, 1), (1, 2), (0, 2)}
        if set(self.edges) != triangle:
            return 0
        a01 = int(self.cochain[(0, 1)])
        a12 = int(self.cochain[(1, 2)])
        a02 = int(self.cochain[(0, 2)])
        return (a01 + a12 - a02) % self.modulus

    def compatible(self) -> bool:
        return self.obstruction() == 0


@dataclass
class WholeCandidate:
    candidate_id: str
    diagram: Diagram
    rho: Array
    hypothesis: str
    declared_marginals: dict[str, Array] | None = None
    parent_candidate: str | None = None
    proposal_kind: str = "initial"
    is_default: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


CUTS: dict[str, tuple[int, ...]] = {
    "S": (0,),
    "E1": (1,),
    "E2": (2,),
    "SE1": (0, 1),
    "SE2": (0, 2),
    "E1E2": (1, 2),
}


def derived_marginals(rho: Array) -> dict[str, Array]:
    return {name: partial_trace(rho, keep) for name, keep in CUTS.items()}


def density_validation(rho: Array) -> dict[str, Any]:
    herm_error = float(np.linalg.norm(rho - dagger(rho)))
    trace_error = abs(float(np.trace(rho).real) - 1.0)
    min_eig = float(np.min(np.linalg.eigvalsh(hermitize(rho))).real)
    return {
        "hermiticity_error": herm_error,
        "trace_error": trace_error,
        "minimum_eigenvalue": min_eig,
        "valid": herm_error <= 1.0e-9 and trace_error <= 1.0e-9 and min_eig >= -1.0e-9,
    }


def global_marginal_witness(candidate: WholeCandidate, tolerance: float = 1.0e-9) -> dict[str, Any]:
    """Verify supplied whole-state witness and all declared restriction maps.

    This is stronger than pairwise overlap checks because the global density
    matrix itself is the feasibility witness.  It does not claim that arbitrary
    pairwise-compatible marginals always possess such a witness.
    """

    density = density_validation(candidate.rho)
    actual = derived_marginals(candidate.rho)
    declared = candidate.declared_marginals or actual
    errors = {name: trace_distance(declared[name], actual[name]) for name in CUTS}
    overlap_errors = {
        "SE1_to_S": trace_distance(partial_trace(declared["SE1"], (0,), (2, 2)), declared["S"]),
        "SE2_to_S": trace_distance(partial_trace(declared["SE2"], (0,), (2, 2)), declared["S"]),
        "E1E2_to_E1": trace_distance(partial_trace(declared["E1E2"], (0,), (2, 2)), declared["E1"]),
        "E1E2_to_E2": trace_distance(partial_trace(declared["E1E2"], (1,), (2, 2)), declared["E2"]),
    }
    max_error = max([*errors.values(), *overlap_errors.values()])
    return {
        "density": density,
        "restriction_errors": errors,
        "overlap_errors": overlap_errors,
        "maximum_error": max_error,
        "globally_consistent": bool(density["valid"] and max_error <= tolerance),
        "witness_dimension": 8,
    }


def settle_candidate(candidate: WholeCandidate, iteration: int) -> dict[str, Any]:
    marginal = global_marginal_witness(candidate)
    topology_ok = candidate.diagram.compatible()
    admitted = bool(marginal["globally_consistent"] and topology_ok)
    sbs = sbs_diagnostics(candidate.rho)
    instrument = instrument_records(candidate.rho)
    return {
        "candidate_id": candidate.candidate_id,
        "diagram_id": candidate.diagram.diagram_id,
        "hypothesis": candidate.hypothesis,
        "parent_candidate": candidate.parent_candidate,
        "proposal_kind": candidate.proposal_kind,
        "is_default": candidate.is_default,
        "iteration": iteration,
        "admitted": admitted,
        "global_marginal_witness": marginal,
        "topology": {
            "modulus": candidate.diagram.modulus,
            "edges": [list(edge) for edge in candidate.diagram.edges],
            "cochain": {f"{a}-{b}": int(value) for (a, b), value in candidate.diagram.cochain.items()},
            "obstruction": candidate.diagram.obstruction(),
            "compatible": topology_ok,
            "parent_diagram": candidate.diagram.parent_diagram,
            "structural_charge": candidate.diagram.structural_charge,
        },
        "sbs": sbs,
        "instrument": {
            "probability_sum": instrument["probability_sum"],
            "completeness_error": instrument["completeness_error"],
            "record_distribution": {
                key: value["probability"] for key, value in instrument["records"].items()
            },
        },
        "state_entropy_vn": entropy_vn(candidate.rho),
        "state_sha256": sha256(np.ascontiguousarray(candidate.rho).view(np.uint8)).hexdigest(),
    }


def greedy_epsilon_cover(states: Sequence[Array], epsilon: float) -> list[int]:
    """Deterministic greedy cover of a finite state set in trace distance."""

    centers: list[int] = []
    uncovered = set(range(len(states)))
    while uncovered:
        center = min(uncovered)
        centers.append(center)
        covered = {j for j in uncovered if trace_distance(states[center], states[j]) <= epsilon}
        uncovered -= covered
    return centers


def finite_extension_fibres(
    candidates: Sequence[WholeCandidate],
    cut: str,
    match_epsilon: float = 0.075,
    cover_epsilon: float = 0.04,
) -> dict[str, Any]:
    """Finite-survivor fibres; no cardinality is assigned to a continuum."""

    keep = CUTS[cut]
    marginals = [partial_trace(c.rho, keep) for c in candidates]
    rows: dict[str, Any] = {}
    for i, candidate in enumerate(candidates):
        members = [j for j, marginal in enumerate(marginals) if trace_distance(marginals[i], marginal) <= match_epsilon]
        member_states = [candidates[j].rho for j in members]
        centers_local = greedy_epsilon_cover(member_states, cover_epsilon)
        rows[candidate.candidate_id] = {
            "cut": cut,
            "match_epsilon": match_epsilon,
            "member_ids": [candidates[j].candidate_id for j in members],
            "finite_cardinality": len(members),
            "hartley_capacity_nats": log(len(members)) if members else float("-inf"),
            "cover_epsilon": cover_epsilon,
            "greedy_cover_count": len(centers_local),
            "greedy_cover_ids": [candidates[members[j]].candidate_id for j in centers_local],
        }
    return rows


OBJECTIVES: tuple[tuple[str, str], ...] = (
    ("system_dephasing_trace_distance", "min"),
    ("max_fragment_root_fidelity", "min"),
    ("conditional_mutual_information_E1_E2_given_S", "min"),
    ("min_fragment_guessing_probability", "max"),
    ("structural_charge", "min"),
)


def objective_vector(settlement: Mapping[str, Any]) -> dict[str, float]:
    return {
        "system_dephasing_trace_distance": float(settlement["sbs"]["system_dephasing_trace_distance"]),
        "max_fragment_root_fidelity": float(settlement["sbs"]["max_fragment_root_fidelity"]),
        "conditional_mutual_information_E1_E2_given_S": float(
            settlement["sbs"]["conditional_mutual_information_E1_E2_given_S"]
        ),
        "min_fragment_guessing_probability": float(
            settlement["sbs"]["min_fragment_guessing_probability"]
        ),
        "structural_charge": float(settlement["topology"]["structural_charge"]),
    }


def dominates(a: Mapping[str, float], b: Mapping[str, float], tol: float = 1.0e-10) -> bool:
    weak = True
    strict = False
    for name, direction in OBJECTIVES:
        av = float(a[name])
        bv = float(b[name])
        if direction == "min":
            weak &= av <= bv + tol
            strict |= av < bv - tol
        else:
            weak &= av >= bv - tol
            strict |= av > bv + tol
    return bool(weak and strict)


def pareto_frontier(settlements: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    admitted = [s for s in settlements if s["admitted"]]
    vectors = {s["candidate_id"]: objective_vector(s) for s in admitted}
    frontier: list[str] = []
    dominated_by: dict[str, list[str]] = {}
    for candidate in admitted:
        cid = candidate["candidate_id"]
        killers = [
            other["candidate_id"]
            for other in admitted
            if other["candidate_id"] != cid and dominates(vectors[other["candidate_id"]], vectors[cid])
        ]
        dominated_by[cid] = killers
        if not killers:
            frontier.append(cid)
    defaults = [s["candidate_id"] for s in admitted if s["is_default"]]
    runnable = list(dict.fromkeys([*frontier, *defaults]))
    incomparable_pairs: list[list[str]] = []
    for left, right in combinations(frontier, 2):
        if not dominates(vectors[left], vectors[right]) and not dominates(vectors[right], vectors[left]):
            incomparable_pairs.append([left, right])
    return {
        "objectives": [{"name": name, "direction": direction} for name, direction in OBJECTIVES],
        "vectors": vectors,
        "frontier_ids": frontier,
        "default_ids": defaults,
        "runnable_ids": runnable,
        "dominated_by": dominated_by,
        "incomparable_frontier_pairs": incomparable_pairs,
        "scalarization_used": False,
    }


def ablation_campaign(initial: Array, stages: Sequence[Stage], full_native: Array) -> dict[str, Any]:
    stages_out: list[dict[str, Any]] = []
    for stage in stages:
        ablated = run_ordered_hypothesis(initial, "H_native", stages, skip_indices=(stage.index,))["rho"]
        full_sbs = sbs_diagnostics(full_native)
        ablated_sbs = sbs_diagnostics(ablated)
        stages_out.append(
            {
                "stage_id": stage.stage_id,
                "trace_distance_from_full": trace_distance(ablated, full_native),
                "delta_min_fragment_guessing_probability": (
                    ablated_sbs["min_fragment_guessing_probability"]
                    - full_sbs["min_fragment_guessing_probability"]
                ),
                "delta_dephasing_trace_distance": (
                    ablated_sbs["system_dephasing_trace_distance"]
                    - full_sbs["system_dephasing_trace_distance"]
                ),
            }
        )
    loop_rows: list[dict[str, Any]] = []
    for engine in (1, 2):
        for loop_name in ("outer", "inner"):
            skipped = [s.index for s in stages if s.engine == engine and s.loop == loop_name]
            ablated = run_ordered_hypothesis(initial, "H_native", stages, skip_indices=skipped)["rho"]
            loop_rows.append(
                {
                    "loop_id": f"E{engine}:{loop_name}",
                    "skipped_indices": skipped,
                    "trace_distance_from_full": trace_distance(ablated, full_native),
                }
            )
    return {
        "stage_deletions": stages_out,
        "loop_deletions": loop_rows,
        "all_stages_load_bearing_at_tolerance_1e-8": all(
            row["trace_distance_from_full"] > 1.0e-8 for row in stages_out
        ),
        "all_loops_load_bearing_at_tolerance_1e-8": all(
            row["trace_distance_from_full"] > 1.0e-8 for row in loop_rows
        ),
    }


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        if np.iscomplexobj(value):
            return {
                "real": value.real.tolist(),
                "imag": value.imag.tolist(),
            }
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def run_campaign() -> dict[str, Any]:
    initial = make_initial_state()
    stages = build_stages()
    ordered = {
        hypothesis: run_ordered_hypothesis(initial, hypothesis, stages)
        for hypothesis in ("H_native", "H_select", "H_all4", "H_mix")
    }
    coherent = run_coherent_history(initial, stages)

    diagram_ok = Diagram(
        diagram_id="triangle_z5_closed",
        edges=((0, 1), (1, 2), (0, 2)),
        modulus=5,
        cochain={(0, 1): 1, (1, 2): 1, (0, 2): 2},
    )
    diagram_bad = Diagram(
        diagram_id="triangle_z5_torn",
        edges=((0, 1), (1, 2), (0, 2)),
        modulus=5,
        cochain={(0, 1): 1, (1, 2): 1, (0, 2): 0},
    )
    diagram_renested = Diagram(
        diagram_id="path_z5_renested",
        edges=((0, 1), (1, 2)),
        modulus=5,
        cochain={(0, 1): 1, (1, 2): 1},
        parent_diagram=diagram_bad.diagram_id,
        structural_charge=1,
    )

    candidates: list[WholeCandidate] = [
        WholeCandidate("default", diagram_ok, initial, "H_default_identity", is_default=True)
    ]
    for hypothesis, result in ordered.items():
        candidates.append(
            WholeCandidate(
                candidate_id=hypothesis,
                diagram=diagram_ok,
                rho=result["rho"],
                hypothesis=hypothesis,
                metadata={"engine_receipt": result},
            )
        )
    candidates.append(
        WholeCandidate(
            candidate_id="H_coherent_history",
            diagram=diagram_ok,
            rho=coherent["rho"],
            hypothesis="H_coherent_history",
            metadata={"coherent_receipt": coherent},
        )
    )
    torn = WholeCandidate(
        candidate_id="H_native_torn",
        diagram=diagram_bad,
        rho=ordered["H_native"]["rho"],
        hypothesis="H_native",
        proposal_kind="topology_control",
    )
    candidates.append(torn)

    iteration0 = [settle_candidate(candidate, 0) for candidate in candidates]

    # The obstruction proposes a different nesting diagram.  The state is not
    # silently declared repaired: the complete candidate is settled again.
    renested = WholeCandidate(
        candidate_id="H_native_renested",
        diagram=diagram_renested,
        rho=torn.rho.copy(),
        hypothesis="H_native",
        parent_candidate=torn.candidate_id,
        proposal_kind="renest_remove_incompatible_cycle_edge",
    )
    candidates.append(renested)
    iteration1 = [settle_candidate(candidate, 1) for candidate in candidates]

    admitted_candidates = [
        candidate for candidate, settlement in zip(candidates, iteration1) if settlement["admitted"]
    ]
    fibres = {
        cut: finite_extension_fibres(admitted_candidates, cut)
        for cut in ("S", "SE1", "SE2")
    }
    frontier = pareto_frontier(iteration1)

    # Marginal-falsification control: preserve a valid global rho but lie about S.
    bad_declared = derived_marginals(initial)
    bad_declared["S"] = X @ bad_declared["S"] @ X
    inconsistent = WholeCandidate(
        "inconsistent_marginal_control",
        diagram_ok,
        initial,
        "control",
        declared_marginals=bad_declared,
    )
    inconsistent_result = settle_candidate(inconsistent, 1)

    native_reversed = run_ordered_hypothesis(initial, "H_native", stages, reverse=True)
    all4_vs_mix = trace_distance(ordered["H_all4"]["rho"], ordered["H_mix"]["rho"])
    native_order_effect = trace_distance(ordered["H_native"]["rho"], native_reversed["rho"])
    ablations = ablation_campaign(initial, stages, ordered["H_native"]["rho"])
    sbs_controls = sbs_falsification_controls(initial)
    boundary_bulk_control = same_boundary_different_bulk_control()

    min_spohn = min(
        result["minimum_spohn"] for result in ordered.values()
    )
    min_dpi = min(result["minimum_dpi_drop"] for result in ordered.values())
    max_invariant_error = max(
        max(result["all_invariant_reference_errors"], default=0.0)
        for result in ordered.values()
    )
    checks = {
        "three_qubit_dimension_is_8": initial.shape == (8, 8),
        "sixteen_stages": len(stages) == 16,
        "eight_stages_per_engine": all(sum(s.engine == e for s in stages) == 8 for e in (1, 2)),
        "all_initial_densities_valid": all(density_validation(c.rho)["valid"] for c in candidates),
        "instrument_complete": instrument_records(initial)["completeness_error"] < 1.0e-12,
        "instrument_probabilities_sum": abs(instrument_records(initial)["probability_sum"] - 1.0) < 1.0e-12,
        "incompatible_cycle_rejected": not next(
            s for s in iteration0 if s["candidate_id"] == "H_native_torn"
        )["admitted"],
        "renesting_reprocessed_and_admitted": next(
            s for s in iteration1 if s["candidate_id"] == "H_native_renested"
        )["admitted"],
        "inconsistent_declared_marginal_rejected": not inconsistent_result["admitted"],
        "spohn_nonnegative_with_invariant_tau": min_spohn >= -1.0e-9,
        "dpi_nonnegative": min_dpi >= -1.0e-9,
        "tau_invariant": max_invariant_error <= 1.0e-10,
        "all4_distinct_from_mix": all4_vs_mix > 1.0e-8,
        "native_order_load_bearing": native_order_effect > 1.0e-8,
        "coherent_history_kept_separate": not coherent["trace_preserving"] and not coherent["ordered_channel_replacement"],
        "pareto_has_runnable_default": "default" in frontier["runnable_ids"],
        "pareto_not_scalarized": not frontier["scalarization_used"],
        "stage_ablation_load_bearing": ablations["all_stages_load_bearing_at_tolerance_1e-8"],
        "loop_ablation_load_bearing": ablations["all_loops_load_bearing_at_tolerance_1e-8"],
        "sbs_record_erasure_control": sbs_controls["checks"]["record_erasure_lowers_min_guessing"],
        "sbs_record_erasure_fidelity_control": sbs_controls["checks"]["record_erasure_raises_fragment_fidelity"],
        "sbs_single_fragment_false_broadcast_control": sbs_controls["checks"]["single_fragment_control_breaks_redundancy"],
        "sbs_phase_scramble_control": sbs_controls["checks"]["phase_scramble_reduces_coherence_residual"],
        "sbs_all_preregistered_controls": sbs_controls["all_checks_pass"],
        "same_boundary_control_is_indistinguishable": boundary_bulk_control["boundary_indistinguishable"],
        "interior_probe_exposes_boundary_compression_loss": boundary_bulk_control["interior_probe_distinguishes"],
    }

    receipt = {
        "schema": "n3-whole-manifold-ratchet-receipt-v1",
        "claim_ceiling": (
            "Executed finite three-qubit calibration only; not a complete entropic-geometric "
            "manifold, proof of MSS, spacetime derivation, or fundamental physics result."
        ),
        "carrier": {
            "subsystems": ["S", "E1", "E2"],
            "hilbert_dimension": 8,
            "density_shape": [8, 8],
            "initial_state_sha256": sha256(np.ascontiguousarray(initial).view(np.uint8)).hexdigest(),
        },
        "engine_chart": [stage.__dict__ | {"stage_id": stage.stage_id} for stage in stages],
        "ordered_hypotheses": {
            name: {
                key: value
                for key, value in result.items()
                if key != "rho"
            }
            for name, result in ordered.items()
        },
        "coherent_history_candidate": {key: value for key, value in coherent.items() if key != "rho"},
        "settlement": {
            "iteration_0": iteration0,
            "iteration_1_full_resettlement": iteration1,
            "renesting_proposal": {
                "from": torn.candidate_id,
                "to": renested.candidate_id,
                "diagram_from": diagram_bad.diagram_id,
                "diagram_to": diagram_renested.diagram_id,
                "structural_charge": diagram_renested.structural_charge,
            },
        },
        "finite_survivor_extension_fibres": fibres,
        "typed_pareto": frontier,
        "ablations": ablations,
        "controls": {
            "inconsistent_marginal": inconsistent_result,
            "all4_vs_mix_trace_distance": all4_vs_mix,
            "native_forward_vs_reverse_trace_distance": native_order_effect,
            "minimum_licensed_spohn": min_spohn,
            "minimum_dpi_drop": min_dpi,
            "maximum_tau_invariance_error": max_invariant_error,
            "sbs_falsification_controls": sbs_controls,
            "same_boundary_different_interior_bulk": boundary_bulk_control,
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    return jsonable(receipt)
