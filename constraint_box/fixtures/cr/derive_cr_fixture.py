#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""Derive the fixed estate schema from an existing CR generator sim."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import scipy.linalg


P = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
SOURCE = Path(
    "/Users/joshuaeisenhart/Codex-Ratchet/"
    "system_v7/constraint_core/sims_and_scripts/nonunitality_theorem_sim.py"
)
OUTPUT = Path(__file__).with_name("cr_gksl_fixture_v1.json")
COMMAND = (
    f"cd {Path(__file__).parent} && {P} {Path(__file__).name}"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source():
    spec = importlib.util.spec_from_file_location("cr_nonunitality_source", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import source sim: {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def superoperator(generator, dimension: int) -> np.ndarray:
    """Return the column-vectorized matrix for the imported generator callable."""
    columns = []
    for col in range(dimension):
        for row in range(dimension):
            basis = np.zeros((dimension, dimension), dtype=complex)
            basis[row, col] = 1
            columns.append(np.asarray(generator(basis)).reshape(-1, order="F"))
    return np.column_stack(columns)


def real_matrix(value: np.ndarray, label: str) -> np.ndarray:
    if np.max(np.abs(np.asarray(value).imag)) > 1e-12:
        raise AssertionError(f"{label} is not real to tolerance: {value}")
    return np.asarray(value).real


def finite_signature(histories):
    present = sorted({row["present"] for row in histories})
    fibres = sorted(
        sum(row["present"] == value for row in histories) for value in present
    )
    return len(histories), present, fibres


def main() -> None:
    sim = load_source()
    dimension = sim.I2.shape[0]

    ti = sim.ops["Ti"]
    te = sim.ops["Te"]
    ti_super = superoperator(ti, dimension)

    # The initial state uses the sim's I2, SX, SZ, and g: the same sim-owned g
    # weights both Bloch axes, making populations unequal without a fixture-only
    # asymmetry constant. Ti comes from sim.ops and preserves real symmetry;
    # sim.kap supplies the evolution duration below.
    rho_initial = (
        sim.I2 + sim.g * sim.SX + sim.g * sim.SZ
    ) / np.trace(sim.I2)
    duration = float(1 / sim.kap)
    rho_vector = scipy.linalg.expm(ti_super * duration) @ rho_initial.reshape(
        -1, order="F"
    )
    rho_array = real_matrix(
        rho_vector.reshape((dimension, dimension), order="F"), "rho"
    )
    assert np.allclose(rho_array, rho_array.T, atol=1e-12, rtol=0.0), (
        f"Ti evolution did not preserve real symmetry: {rho_array}"
    )

    # Extract Ti's coherence decay eigenvalue by its action on SX, then confirm
    # that the extracted value belongs to the superoperator spectrum.
    sx_image = real_matrix(ti(sim.SX), "Ti(SX)")
    flow_rate = float(
        np.vdot(sim.SX, sx_image).real / np.vdot(sim.SX, sim.SX).real
    )
    ti_spectrum = np.linalg.eigvals(ti_super)
    assert min(abs(value - flow_rate) for value in ti_spectrum) < 1e-12
    assert np.allclose(sx_image, flow_rate * sim.SX)

    # Te applied to the first population basis state supplies the symmetric
    # population-mixing rate; no Te coefficient is repeated here.
    population_basis = np.zeros_like(sim.I2)
    population_basis[0, 0] = 1
    te_population = real_matrix(te(population_basis), "Te(E00)")
    channel_gamma = float(te_population[1, 1])
    assert np.allclose(
        te_population,
        [[-channel_gamma, 0.0], [0.0, channel_gamma]],
    )

    # One actual matrix-exponential application is the sole discrete step.
    # Its input is exactly sim.SX, so discrete_rate.initial is ||sim.SX||_F.
    step_input = sim.SX
    steps_taken = 1
    step_image = scipy.linalg.expm(ti_super * duration) @ step_input.reshape(
        -1, order="F"
    )
    step_matrix = real_matrix(
        step_image.reshape((dimension, dimension), order="F"), "Ti step on SX"
    )
    multiplier = float(
        np.vdot(sim.SX, step_matrix).real / np.vdot(sim.SX, sim.SX).real
    )

    # Each history is one literal terrain row: past=eps, present=pole,
    # future=kind. The sim supplies a keyed table, not a temporal ordering; the
    # fixture enumerates its insertion-order rows without claiming chronology.
    histories = [
        {"past": int(eps), "present": int(pole), "future": str(kind)}
        for eps, pole, kind in sim.terr.values()
    ]

    rho = [[float(value) for value in row] for row in rho_array]
    dephased = [
        [rho[0][0], 0.0],
        [0.0, rho[1][1]],
    ]
    fixture = {
        "schema": "constraintbox.manifold-fixture.v1",
        "rho": rho,
        "dephased": dephased,
        "flow": {
            "initial": float(abs(rho_initial[0, 1])),
            "rate": flow_rate,
            "duration": duration,
        },
        "channel": {
            "gamma": channel_gamma,
            "duration": duration,
        },
        "discrete_rate": {
            "initial": float(np.linalg.norm(step_input)),
            "multiplier": multiplier,
            "steps": steps_taken,
        },
        "finite_histories": histories,
        "provenance": {
            "source_sim": str(SOURCE),
            "source_sim_sha256": sha256(SOURCE),
            "derivation_script_sha256": sha256(Path(__file__)),
            "command": COMMAND,
            "finite_histories_mapping": {
                "past": "eps",
                "present": "pole",
                "future": "kind (string)",
                "source_rows": "sim.terr insertion order",
                "chronology_claimed": False,
                "semantic_limit": (
                    "keyed terrain-table rows relabeled as a finite triple; "
                    "no chronology is claimed"
                ),
            },
            "discrete_rate_mapping": {
                "initial": "Frobenius norm of sim.SX, the actual step input",
                "steps": "one matrix-exponential application actually performed",
            },
        },
        "claim_ceiling": "finite acceptance fixture only",
        "promotion_allowed": False,
    }

    # C1: the density state is real symmetric, normalized, PSD, and full rank.
    rho_check = np.asarray(fixture["rho"], dtype=float)
    assert rho_check.shape == (dimension, dimension)
    assert np.array_equal(rho_check, rho_check.T)
    assert abs(float(np.trace(rho_check)) - 1.0) <= 1e-12
    eigenvalues = np.linalg.eigvalsh(rho_check)
    assert np.all(eigenvalues >= -1e-12)
    assert np.all(eigenvalues > 1e-12)

    # C2: the supplied dephasing is exactly the diagonal read by the worker.
    assert fixture["dephased"] == [
        [fixture["rho"][0][0], 0.0],
        [0.0, fixture["rho"][1][1]],
    ]

    # C3: every acceptance overwrite differs, and the overwritten rho is PSD.
    assert abs(fixture["rho"][0][1] - 0.125) > 1e-3
    assert abs(fixture["flow"]["rate"] - (-1.5)) > 1e-3
    assert abs(fixture["discrete_rate"]["multiplier"] - 0.4) > 1e-3
    assert abs(fixture["channel"]["gamma"] - 0.5) > 1e-3
    mutated_rho = rho_check.copy()
    mutated_rho[0, 1] = mutated_rho[1, 0] = 0.125
    mutated_eigenvalues = np.linalg.eigvalsh(mutated_rho)
    assert np.all(mutated_eigenvalues >= -1e-12)
    assert finite_signature(histories) != finite_signature(histories[:-1])

    # C4: signs, contraction range, and finite-history diversity.
    assert fixture["flow"]["rate"] < 0
    assert fixture["channel"]["gamma"] > 0
    assert 0 < fixture["discrete_rate"]["multiplier"] < 1
    assert len(histories) >= 4
    assert len({row["present"] for row in histories}) >= 2

    # C5: unequal populations prevent the degenerate one-bit entropy maximum
    # and make an index-swapped diagonal read observable.
    population_gap = abs(fixture["rho"][0][0] - fixture["rho"][1][1])
    diagonal_probabilities = np.diag(rho_check)
    dephased_entropy_bits = float(
        -sum(
            probability * math.log2(probability)
            for probability in diagonal_probabilities
            if probability > 0
        )
    )
    assert population_gap > 1e-3
    assert dephased_entropy_bits < 0.999

    OUTPUT.write_text(
        json.dumps(
            fixture,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    receipt = {
        "C1": {
            "rho": fixture["rho"],
            "trace": float(np.trace(rho_check)),
            "eigenvalues": [float(value) for value in eigenvalues],
            "rank": int(sum(value > 1e-12 for value in eigenvalues)),
        },
        "C2": {"dephased": fixture["dephased"]},
        "C3": {
            "rho_offdiag": fixture["rho"][0][1],
            "flow_rate": fixture["flow"]["rate"],
            "discrete_multiplier": fixture["discrete_rate"]["multiplier"],
            "channel_gamma": fixture["channel"]["gamma"],
            "mutated_rho_eigenvalues": [
                float(value) for value in mutated_eigenvalues
            ],
            "history_signature": finite_signature(histories),
            "mutated_history_signature": finite_signature(histories[:-1]),
        },
        "C4": {
            "history_count": len(histories),
            "distinct_present": sorted({row["present"] for row in histories}),
        },
        "C5": {
            "population_gap": population_gap,
            "dephased_entropy_bits": dephased_entropy_bits,
        },
        "provenance": fixture["provenance"],
        "output": str(OUTPUT),
    }
    print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
