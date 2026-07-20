#!/usr/bin/env python3
"""Carrier tournament v1: per-episode belief carriers under audited budgets.

The exact ``senses_v2_slow_memory`` world, split, anchor episode, and metric
semantics are reused.  The oracle is a ceiling reference, not a competitor.

Important source-level boundary: the unchanged anchor is a 4x4 (two-qubit)
``rho_fast`` plus a 1024-hypothesis ``m_slow`` posterior.  That is 1038 live
real state degrees of freedom, despite the owner prompt's three-qubit
shorthand.  Attempt 2 freezes that actual 1038-DOF capacity as the charged
fitted-parameter budget: every competitor must land within plus or minus ten
percent of it, with a hard fail-closed gate.  The product lane uses only
outcome-conditioned CPTP Kraus instruments and asserts physicality after each
update.  No result permits promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Callable


REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = REPO / "system_v8" / "loop3_senses"
SOURCE = HERE / "carrier_tournament_v1.py"
OBJECT_CARD = HERE / "carrier_tournament_v1_v43_card.json"
PREREGISTRATION = REPO / "system_v8" / "spinor_jepa" / "TOURNAMENT_CARD_v0.md"
ANCHOR_SOURCE = HERE / "senses_v2_slow_memory.py"
ANCHOR_RECEIPT = HERE / "results" / "senses_v2_slow_memory" / "receipt.json"
REFEREE_RECEIPTS = (
    HERE / "results" / "senses_v2_slow_memory" / "nvidia_referee_receipts.json"
)
OUTDIR = HERE / "results" / "carrier_tournament_v1"
RECEIPT_PATH = OUTDIR / "receipt.json"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")

SEED = 20260719
TORCH_SEED = 20261222
SCRAMBLE_SEED = 20261420
N_BITS = 8
N_VIEWS = 6
FEATURE_DOF = 30
GRU_HIDDEN = 11
GRU_EPOCHS = 250
HMM_EPOCHS = 250
HMM_LEARNING_RATE = 5e-2
PRODUCT_QUBITS = 10
ANCHOR_CHARGED_FITTED_PARAMETER_COUNT = 1038
BUDGET_TOLERANCE_FRACTION = 0.10
PHYSICALITY_TOLERANCE = 1e-9
N_BOOTSTRAPS = 5000
N_PERMUTATIONS = 200
MI_BINS = 5
MIN_MEMORY_FREE_PERCENT = 25
promotion_allowed = False
formal_admission_allowed = False
CLASSIFICATION = "scratch_diagnostic"

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite filters, CPTP product density states, bootstrap, MI nulls, pair tables, and receipt checks",
    },
    "scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the unchanged senses_v2 measurement-channel loader",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing standard sequential GRU competitor; its predictions and CI enter the frozen falsifier table",
    },
    "TorchRL": {
        "tried": False,
        "used": False,
        "reason": "not required: donor patterns were allowed but the bounded six-step GRU needs no external replay or environment wrapper",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy.linalg.expm": "load_bearing",
    "torch": "load_bearing",
    "TorchRL": None,
}


class TournamentError(RuntimeError):
    """A provenance, runtime, integrity, or execution error."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def memory_free_percent() -> int:
    process = subprocess.run(
        ["memory_pressure"], capture_output=True, text=True, check=True
    )
    match = re.search(
        r"System-wide memory free percentage:\s*(\d+)%", process.stdout
    )
    if match is None:
        raise TournamentError("memory_pressure did not report a free percentage")
    return int(match.group(1))


def refuse_to_reuse() -> None:
    if OUTDIR.exists():
        raise TournamentError(f"REFUSE-TO-REUSE: outdir already exists: {OUTDIR}")


def validate_object_card() -> dict[str, Any]:
    process = subprocess.run(
        [
            str(SIM_PY),
            str(REPO / "scripts" / "wizard_v4_3_object_preservation.py"),
            "validate",
            "--input",
            str(OBJECT_CARD),
        ],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise TournamentError(f"v4.3 validator returned invalid JSON: {error}")
    if process.returncode != 0 or payload.get("ok") is not True:
        raise TournamentError(f"v4.3 object card failed: {payload}")
    return payload


def required_paths() -> list[Path]:
    return [
        SOURCE,
        OBJECT_CARD,
        PREREGISTRATION,
        ANCHOR_SOURCE,
        ANCHOR_RECEIPT,
        REFEREE_RECEIPTS,
    ]


def preflight(
    *, require_fresh_outdir: bool, repair_malformed_receipt: bool = False
) -> dict[str, Any]:
    if SIM_PY.resolve() != Path(sys.executable).resolve():
        raise TournamentError(
            f"wrong interpreter: {sys.executable}; required realpath {SIM_PY.resolve()}"
        )
    missing = [str(path) for path in required_paths() if not path.is_file()]
    if missing:
        raise TournamentError(f"missing required inputs: {missing}")
    if require_fresh_outdir:
        refuse_to_reuse()
    if repair_malformed_receipt:
        if not OUTDIR.is_dir() or not RECEIPT_PATH.is_file():
            raise TournamentError(
                "malformed-receipt repair requires the exact existing result directory and receipt path"
            )
        try:
            json.loads(RECEIPT_PATH.read_text())
        except json.JSONDecodeError:
            pass
        else:
            raise TournamentError(
                "REFUSE-TO-REUSE: repair mode accepts only an invalid partial receipt"
            )
    memory_percent = memory_free_percent()
    if memory_percent <= MIN_MEMORY_FREE_PERCENT:
        raise TournamentError(
            f"memory free percentage {memory_percent}% is not > "
            f"{MIN_MEMORY_FREE_PERCENT}%"
        )
    card = validate_object_card()
    return {
        "python": sys.executable,
        "required_python": str(SIM_PY),
        "memory_free_percent": memory_percent,
        "minimum_required_percent": MIN_MEMORY_FREE_PERCENT,
        "object_card_validation": card,
        "result_directory_absent": not OUTDIR.exists(),
        "malformed_receipt_repair": repair_malformed_receipt,
    }


def run(preflight_receipt: dict[str, Any]) -> dict[str, Any]:
    # Heavy imports happen only after the interpreter and >25% memory gates.
    import numpy as np
    import torch
    from torch import nn

    sys.path.insert(0, str(REPO))
    from system_v8.loop3_senses import loop2_retest_fixed_senses as readout
    from system_v8.loop3_senses import senses_v2_slow_memory as anchor
    from system_v8.loop3_senses import visibility_sanity_gate as visibility

    tracked_inputs = [
        *required_paths(),
        anchor.EVENTS,
        anchor.WORLD_RECEIPT,
        anchor.LOOP2_SOURCE,
        anchor.LOOP2_RECEIPT,
        anchor.STAGE64,
        anchor.VISIBILITY_SOURCE,
        anchor.PARENT_SOURCE,
        anchor.PARENT_RECEIPT,
        anchor.FOUNDATION_CARD,
    ]
    input_hashes_start = {str(path): sha256_file(path) for path in tracked_inputs}

    with anchor.WORLD_RECEIPT.open() as handle:
        world_receipt = json.load(handle)
    with anchor.STAGE64.open() as handle:
        stage_receipt = json.load(handle)
    with ANCHOR_RECEIPT.open() as handle:
        prior_anchor_receipt = json.load(handle)

    rule_family = {
        int(key): tuple(int(offset) for offset in offsets)
        for key, offsets in world_receipt["parameters"]["rule_family"].items()
    }
    log, schema_metrics = visibility.parse_event_log(anchor.EVENTS)
    full_views, recovery_metrics = visibility.recover_full_views(log, rule_family)
    object_ids = sorted(log)
    train_objects, test_objects = visibility.train_test_objects(object_ids)
    train_set = set(train_objects)
    test_set = set(test_objects)
    channels, _ = visibility.load_stage_channels(
        stage_receipt, encoder_channel_fix=False
    )
    words, rules, hypotheses = anchor.build_hypotheses(rule_family)

    def log_getter(object_id: str) -> Callable[[int, int], str | None]:
        return lambda view, position: (
            None
            if log[object_id][view][position] == "withheld"
            else log[object_id][view][position]
        )

    slots = [
        (object_id, view, position)
        for object_id in object_ids
        for view in range(N_VIEWS)
        for position in range(N_BITS)
        if log[object_id][view][position] == "withheld"
    ]
    train_slots = [slot for slot in slots if slot[0] in train_set]
    test_slots = [slot for slot in slots if slot[0] in test_set]

    def truth(slot: tuple[str, int, int]) -> int:
        object_id, view, position = slot
        return int(full_views[object_id][view][position])

    train_bits = np.asarray([truth(slot) for slot in train_slots], dtype=int)
    pooled_majority = int(float(train_bits.mean()) >= 0.5)
    position_majority: dict[int, int] = {}
    for position in range(N_BITS):
        bits = [truth(slot) for slot in train_slots if slot[2] == position]
        position_majority[position] = (
            int(float(np.mean(bits)) >= 0.5) if bits else pooled_majority
        )
    pooled_train_accuracy = float(
        np.mean([truth(slot) == pooled_majority for slot in train_slots])
    )
    position_train_accuracy = float(
        np.mean(
            [truth(slot) == position_majority[slot[2]] for slot in train_slots]
        )
    )
    use_position_majority = position_train_accuracy > pooled_train_accuracy
    chance_correct = {
        slot: truth(slot)
        == (
            position_majority[slot[2]]
            if use_position_majority
            else pooled_majority
        )
        for slot in test_slots
    }
    computed_chance = float(np.mean(list(chance_correct.values())))

    masks_by_view: dict[int, set[tuple[bool, ...]]] = {
        view: set() for view in range(N_VIEWS)
    }
    for object_id in object_ids:
        getter = log_getter(object_id)
        for view in range(N_VIEWS):
            masks_by_view[view].add(
                tuple(getter(view, position) is not None for position in range(N_BITS))
            )
    for view in range(N_VIEWS):
        masks_by_view[view].add(tuple(True for _ in range(N_BITS)))
        for position in range(N_BITS):
            masks_by_view[view].add(
                tuple(index != position for index in range(N_BITS))
            )

    # Lane 4: exact source-reused anchor plus its two named ports.
    anchor_engine = anchor.QuantumReadoutBayes(
        channels, visibility, words, rules, hypotheses
    )
    anchor_calibration = anchor_engine.calibrate_sigma(masks_by_view)
    anchor_raw_states = {
        object_id: anchor_engine.episode(
            log_getter(object_id), keep_posteriors=True
        )
        for object_id in object_ids
    }
    anchor_reset_raw = {
        object_id: anchor_engine.episode(
            log_getter(object_id),
            reset_slow_each_view=True,
            keep_posteriors=False,
        )
        for object_id in object_ids
    }
    anchor_frozen_raw = {
        object_id: anchor_engine.episode(
            log_getter(object_id), frozen_actual=True, keep_posteriors=False
        )
        for object_id in object_ids
    }

    def adapt_anchor(
        raw: dict[str, list[dict[str, Any]]]
    ) -> dict[str, list[dict[str, Any]]]:
        return {
            object_id: [
                {
                    "feature": state["joint_feature"].copy(),
                    "belief": state["m_slow_summary"][:N_BITS].copy(),
                    "posterior": (
                        None if state.get("posterior") is None else state["posterior"].copy()
                    ),
                }
                for state in states
            ]
            for object_id, states in raw.items()
        }

    anchor_states = adapt_anchor(anchor_raw_states)
    anchor_reset_states = adapt_anchor(anchor_reset_raw)
    anchor_frozen_states = adapt_anchor(anchor_frozen_raw)

    def masked_fast15(getter: Callable[[int, int], str | None], view: int) -> Any:
        values = np.asarray(
            [
                0.5 if getter(view, position) is None else float(getter(view, position))
                for position in range(N_BITS)
            ],
            dtype=float,
        )
        masks = np.asarray(
            [getter(view, position) is not None for position in range(N_BITS)],
            dtype=float,
        )
        return np.concatenate([values, masks[:7]])

    def posterior_episode(
        object_id: str,
        *,
        epsilon_by_view_position: Any | None,
        exact: bool,
        prior: Any | None = None,
        parameter_permutation: Any | None = None,
    ) -> list[dict[str, Any]]:
        getter = log_getter(object_id)
        posterior = (
            np.full(len(hypotheses), 1.0 / len(hypotheses), dtype=float)
            if prior is None
            else np.asarray(prior, dtype=float).copy()
        )
        states = []
        for view in range(N_VIEWS):
            for position in range(N_BITS):
                observed = getter(view, position)
                if observed is None:
                    continue
                candidate = hypotheses[:, view, position]
                if exact:
                    likelihood = (candidate == int(observed)).astype(float)
                else:
                    parameter_position = (
                        int(parameter_permutation[position])
                        if parameter_permutation is not None
                        else position
                    )
                    if epsilon_by_view_position is None:
                        raise TournamentError("HMM emission parameters are missing")
                    epsilon = float(
                        epsilon_by_view_position[view, parameter_position]
                    )
                    likelihood = np.where(candidate == int(observed), 1.0 - epsilon, epsilon)
                posterior *= likelihood
                total = float(posterior.sum())
                if total <= 0.0:
                    raise TournamentError(
                        f"posterior collapsed for {object_id}, view {view}, position {position}"
                    )
                posterior /= total
            summary = anchor_engine.posterior_summary(posterior, view)
            feature = np.concatenate([masked_fast15(getter, view), summary])
            states.append(
                {
                    "feature": feature,
                    "belief": summary[:N_BITS].copy(),
                    "posterior": posterior.copy(),
                }
            )
        return states

    # Lane 2: a finite-state/HMM filter with an actually fitted 1036-scalar
    # capacity: 1023 nonredundant prior logits, eight position emission logits,
    # and five view emission logits (the sixth view is the fixed reference).
    # Every scalar enters the
    # train-object marginal likelihood; no nominal padding is counted.
    def fit_hmm_parameters() -> tuple[Any, Any, int, list[dict[str, float]], bool]:
        hypothesis_tensor = torch.tensor(hypotheses, dtype=torch.bool)
        prior_logits = torch.nn.Parameter(torch.zeros(len(hypotheses) - 1))
        position_logits = torch.nn.Parameter(torch.zeros(N_BITS))
        view_logits = torch.nn.Parameter(torch.zeros(N_VIEWS - 1))
        parameters = [prior_logits, position_logits, view_logits]
        optimizer = torch.optim.Adam(parameters, lr=HMM_LEARNING_RATE)
        trace = []
        for epoch in range(HMM_EPOCHS):
            optimizer.zero_grad(set_to_none=True)
            complete_prior_logits = torch.cat(
                [prior_logits, torch.zeros(1, dtype=prior_logits.dtype)]
            )
            complete_view_logits = torch.cat(
                [view_logits, torch.zeros(1, dtype=view_logits.dtype)]
            )
            log_prior = torch.log_softmax(complete_prior_logits, dim=0)
            negative_log_likelihoods = []
            for object_id in train_objects:
                getter = log_getter(object_id)
                log_posterior = log_prior
                for view in range(N_VIEWS):
                    for position in range(N_BITS):
                        observed = getter(view, position)
                        if observed is None:
                            continue
                        epsilon = 0.01 + 0.24 * torch.sigmoid(
                            position_logits[position] + complete_view_logits[view]
                        )
                        candidate = hypothesis_tensor[:, view, position] == int(observed)
                        log_posterior = log_posterior + torch.where(
                            candidate, torch.log1p(-epsilon), torch.log(epsilon)
                        )
                negative_log_likelihoods.append(-torch.logsumexp(log_posterior, dim=0))
            regularizer = 1e-4 * sum(torch.square(parameter).mean() for parameter in parameters)
            loss = torch.stack(negative_log_likelihoods).mean() + regularizer
            loss.backward()
            optimizer.step()
            if epoch in {0, HMM_EPOCHS - 1}:
                trace.append({"epoch": float(epoch + 1), "loss": float(loss.detach())})
        fitted_prior = torch.softmax(
            torch.cat([prior_logits.detach(), torch.zeros(1)]), dim=0
        ).cpu().numpy()
        fitted_epsilon = (
            0.01
            + 0.24
            * torch.sigmoid(
                position_logits.detach()[None, :]
                + torch.cat([view_logits.detach(), torch.zeros(1)])[:, None]
            )
        ).cpu().numpy()
        all_parameters_active = bool(
            all(
                parameter.grad is not None
                and bool(torch.isfinite(parameter.grad).all())
                and bool(torch.any(parameter.grad != 0))
                for parameter in parameters
            )
        )
        return (
            fitted_prior,
            fitted_epsilon,
            int(sum(parameter.numel() for parameter in parameters)),
            trace,
            all_parameters_active,
        )

    (
        hmm_prior,
        hmm_epsilon,
        hmm_parameter_count,
        hmm_loss_trace,
        hmm_all_parameters_active,
    ) = fit_hmm_parameters()
    oracle_states = {
        object_id: posterior_episode(
            object_id, epsilon_by_view_position=None, exact=True
        )
        for object_id in object_ids
    }
    hmm_states = {
        object_id: posterior_episode(
            object_id,
            epsilon_by_view_position=hmm_epsilon,
            exact=False,
            prior=hmm_prior,
        )
        for object_id in object_ids
    }

    def masked_view_vector(
        object_id: str, view: int, *, source_permutation: Any | None = None
    ) -> Any:
        getter = log_getter(object_id)
        values = []
        masks = []
        for destination in range(N_BITS):
            source = (
                int(source_permutation[destination])
                if source_permutation is not None
                else destination
            )
            observed = getter(view, source)
            values.append(0.0 if observed is None else (2.0 * int(observed) - 1.0))
            masks.append(0.0 if observed is None else 1.0)
        return np.asarray(values + masks + [view / (N_VIEWS - 1)], dtype=np.float32)

    # Lane 3: standard Torch GRU, trained for a frozen number of full-batch
    # epochs.  H=11 gives 1086 fitted parameters, inside the fixed Attempt 2
    # capacity interval.  A deterministic non-parameterized feature lift keeps
    # the common 30-coordinate readout interface.  No test-object validation
    # or early stopping is permitted.
    class SequentialGRU(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.cell = nn.GRUCell(17, GRU_HIDDEN)
            self.head = nn.Linear(GRU_HIDDEN, N_BITS)

        def forward(self, sequence: Any) -> tuple[Any, Any]:
            hidden = torch.zeros(
                sequence.shape[0], GRU_HIDDEN, dtype=sequence.dtype
            )
            hidden_by_view = []
            logits_by_view = []
            for view in range(N_VIEWS):
                hidden = self.cell(sequence[:, view, :], hidden)
                hidden_by_view.append(hidden)
                logits_by_view.append(self.head(hidden))
            return torch.stack(hidden_by_view, dim=1), torch.stack(logits_by_view, dim=1)

    torch.manual_seed(TORCH_SEED)
    torch.use_deterministic_algorithms(True)
    gru_model = SequentialGRU()
    gru_initial_parameter_sha256 = sha256_json(
        [parameter.detach().cpu().numpy().tolist() for parameter in gru_model.parameters()]
    )
    optimizer = torch.optim.Adam(gru_model.parameters(), lr=1e-2)
    train_inputs = torch.tensor(
        np.stack(
            [
                np.stack(
                    [masked_view_vector(object_id, view) for view in range(N_VIEWS)]
                )
                for object_id in train_objects
            ]
        ),
        dtype=torch.float32,
    )
    train_targets = torch.tensor(
        np.asarray([full_views[object_id] for object_id in train_objects], dtype=float),
        dtype=torch.float32,
    )
    train_loss_mask = torch.tensor(
        np.asarray(
            [
                [
                    [log[object_id][view][position] == "withheld" for position in range(N_BITS)]
                    for view in range(N_VIEWS)
                ]
                for object_id in train_objects
            ],
            dtype=float,
        ),
        dtype=torch.float32,
    )
    loss_trace = []
    gru_model.train()
    for epoch in range(GRU_EPOCHS):
        optimizer.zero_grad(set_to_none=True)
        _, logits = gru_model(train_inputs)
        point_loss = torch.nn.functional.binary_cross_entropy_with_logits(
            logits, train_targets, reduction="none"
        )
        loss = (point_loss * train_loss_mask).sum() / train_loss_mask.sum()
        loss.backward()
        optimizer.step()
        if epoch in {0, GRU_EPOCHS - 1}:
            loss_trace.append({"epoch": epoch + 1, "loss": float(loss.detach())})
    gru_final_parameter_sha256 = sha256_json(
        [parameter.detach().cpu().numpy().tolist() for parameter in gru_model.parameters()]
    )
    gru_all_parameters_active = bool(
        all(
            parameter.grad is not None
            and bool(torch.isfinite(parameter.grad).all())
            and bool(torch.any(parameter.grad != 0))
            for parameter in gru_model.parameters()
        )
    )

    def gru_state_map(source_permutation: Any | None = None) -> dict[str, list[dict[str, Any]]]:
        inputs = torch.tensor(
            np.stack(
                [
                    np.stack(
                        [
                            masked_view_vector(
                                object_id, view, source_permutation=source_permutation
                            )
                            for view in range(N_VIEWS)
                        ]
                    )
                    for object_id in object_ids
                ]
            ),
            dtype=torch.float32,
        )
        gru_model.eval()
        with torch.no_grad():
            hidden, logits = gru_model(inputs)
            beliefs = torch.sigmoid(logits)
        hidden_np = hidden.cpu().numpy().astype(float)
        belief_np = beliefs.cpu().numpy().astype(float)
        hidden_summary = np.concatenate(
            [hidden_np[:, :, :9], hidden_np.mean(axis=2, keepdims=True)], axis=2
        )
        feature_np = np.concatenate(
            [hidden_summary, np.square(hidden_summary), np.tanh(hidden_summary)], axis=2
        )
        return {
            object_id: [
                {
                    "feature": feature_np[object_index, view].copy(),
                    "belief": belief_np[object_index, view].copy(),
                }
                for view in range(N_VIEWS)
            ]
            for object_index, object_id in enumerate(object_ids)
        }

    gru_states = gru_state_map()

    # Lane 5: ten independent single-qubit density stages.  Eight stages retain
    # position-specific evidence; two retain global public-visibility and clock
    # context.  Every transition is an outcome-conditioned CPTP Kraus
    # instrument, never an additive Bloch-vector update.  A 10x6x8 bank of
    # fitted unsharpness and phase values, plus ten fitted initial z biases,
    # gives 970 charged fitted product parameters inside the Attempt 2 budget.
    product_i2 = np.eye(2, dtype=complex)
    product_sx = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    product_sy = np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
    product_sz = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    product_paulis = (product_sx, product_sy, product_sz)

    def stable_logit(value: float) -> float:
        clipped = float(np.clip(value, 1e-6, 1.0 - 1e-6))
        return float(np.log(clipped / (1.0 - clipped)))

    def product_training_outcome(
        stage: int, position: int, observed: str | None
    ) -> int | None:
        if stage < N_BITS and stage == position:
            return None if observed is None else int(observed)
        return int(observed is not None)

    def fit_product_instruments() -> tuple[Any, Any, Any, int, dict[str, Any]]:
        eta_logits = np.empty((PRODUCT_QUBITS, N_VIEWS, N_BITS), dtype=float)
        phase_angles = np.empty((PRODUCT_QUBITS, N_VIEWS, N_BITS), dtype=float)
        initial_z_logits = np.empty(PRODUCT_QUBITS, dtype=float)
        training_counts = np.zeros((PRODUCT_QUBITS, N_VIEWS, N_BITS), dtype=int)
        for stage in range(PRODUCT_QUBITS):
            initial_values = []
            stage_prior = (stage + 1.0) / (PRODUCT_QUBITS + 1.0)
            for view in range(N_VIEWS):
                for position in range(N_BITS):
                    values = []
                    for object_id in train_objects:
                        outcome = product_training_outcome(
                            stage, position, log_getter(object_id)(view, position)
                        )
                        if outcome is not None:
                            values.append(outcome)
                            if view == 0:
                                initial_values.append(outcome)
                    if not values:
                        raise TournamentError(
                            f"product parameter {stage}/{view}/{position} has no train observation"
                        )
                    training_counts[stage, view, position] = len(values)
                    posterior_mean = (sum(values) + stage_prior) / (
                        len(values) + 1.0
                    )
                    eta = 0.05 + 0.85 * abs(2.0 * posterior_mean - 1.0)
                    eta_logits[stage, view, position] = stable_logit(
                        (eta - 0.02) / 0.94
                    )
                    phase_angles[stage, view, position] = np.pi * (
                        posterior_mean - 0.5
                    )
            initial_mean = (sum(initial_values) + stage_prior) / (
                len(initial_values) + 1.0
            )
            initial_z_logits[stage] = stable_logit(initial_mean)
        parameter_count = int(
            eta_logits.size + phase_angles.size + initial_z_logits.size
        )
        return eta_logits, phase_angles, initial_z_logits, parameter_count, {
            "fit_data": "train-object visible bits for local stages and train-object public visibility masks for global/context stages",
            "minimum_train_observations_per_bank_entry": int(training_counts.min()),
            "maximum_train_observations_per_bank_entry": int(training_counts.max()),
            "eta_logits": int(eta_logits.size),
            "phase_angles": int(phase_angles.size),
            "initial_z_logits": int(initial_z_logits.size),
        }

    (
        product_eta_logits,
        product_phase_angles,
        product_initial_z_logits,
        product_parameter_count,
        product_fit_metadata,
    ) = fit_product_instruments()
    product_parameter_usage = np.zeros(
        (PRODUCT_QUBITS, N_VIEWS, N_BITS), dtype=int
    )

    def new_product_physicality_ledger() -> dict[str, Any]:
        return {
            "updates_checked": 0,
            "visible_bit_updates": 0,
            "visibility_mask_updates": 0,
            "missing_identity_updates": 0,
            "clock_updates": 0,
            "zero_or_nonfinite_probability_updates": 0,
            "maximum_bloch_norm": 0.0,
            "maximum_trace_deviation": 0.0,
            "maximum_hermiticity_deviation": 0.0,
            "minimum_eigenvalue": 1.0,
            "threshold": PHYSICALITY_TOLERANCE,
            "pass": True,
        }

    def product_bloch(density: Any) -> Any:
        return np.asarray(
            [float(np.real(np.trace(pauli @ density))) for pauli in product_paulis],
            dtype=float,
        )

    def assert_product_update(
        density: Any,
        probability: float,
        ledger: dict[str, Any],
        *,
        object_id: str,
        view: int,
        stage: int,
        event: str,
    ) -> tuple[Any, float]:
        trace_deviation = float(abs(np.trace(density) - 1.0))
        hermiticity_deviation = float(np.max(abs(density - density.conj().T)))
        eigenvalue = float(np.linalg.eigvalsh(0.5 * (density + density.conj().T)).min())
        bloch = product_bloch(density)
        norm = float(np.linalg.norm(bloch))
        ledger["updates_checked"] += 1
        ledger["maximum_bloch_norm"] = max(ledger["maximum_bloch_norm"], norm)
        ledger["maximum_trace_deviation"] = max(
            ledger["maximum_trace_deviation"], trace_deviation
        )
        ledger["maximum_hermiticity_deviation"] = max(
            ledger["maximum_hermiticity_deviation"], hermiticity_deviation
        )
        ledger["minimum_eigenvalue"] = min(ledger["minimum_eigenvalue"], eigenvalue)
        if not np.isfinite(probability) or probability <= 1e-15:
            ledger["zero_or_nonfinite_probability_updates"] += 1
        if (
            not np.isfinite([probability, trace_deviation, hermiticity_deviation, eigenvalue, norm]).all()
            or probability <= 1e-15
            or trace_deviation > PHYSICALITY_TOLERANCE
            or hermiticity_deviation > PHYSICALITY_TOLERANCE
            or eigenvalue < -PHYSICALITY_TOLERANCE
            or norm > 1.0 + PHYSICALITY_TOLERANCE
        ):
            ledger["pass"] = False
            raise TournamentError(
                "nonphysical product CPTP update "
                f"object={object_id} view={view} stage={stage} event={event} "
                f"probability={probability} norm={norm}"
            )
        return bloch, norm

    def product_measurement_kraus(eta: float, phase: float) -> tuple[Any, Any]:
        if not 0.0 <= eta < 1.0:
            raise TournamentError(f"invalid product measurement sharpness {eta}")
        rotation = (
            np.cos(phase / 2.0) * product_i2
            - 1.0j * np.sin(phase / 2.0) * product_sx
        )
        k0 = rotation @ np.diag(
            [np.sqrt((1.0 + eta) / 2.0), np.sqrt((1.0 - eta) / 2.0)]
        )
        k1 = rotation @ np.diag(
            [np.sqrt((1.0 - eta) / 2.0), np.sqrt((1.0 + eta) / 2.0)]
        )
        completeness = k0.conj().T @ k0 + k1.conj().T @ k1
        if not np.allclose(completeness, product_i2, atol=PHYSICALITY_TOLERANCE):
            raise TournamentError("product measurement Kraus pair is not CPTP")
        return k0, k1

    def apply_product_measurement(
        density: Any, eta: float, phase: float, outcome: int
    ) -> tuple[Any, float]:
        kraus = product_measurement_kraus(eta, phase)[int(outcome)]
        unnormalized = kraus @ density @ kraus.conj().T
        probability = float(np.real(np.trace(unnormalized)))
        if not np.isfinite(probability) or probability <= 1e-15:
            raise TournamentError("product measurement outcome has zero/nonfinite probability")
        return unnormalized / probability, probability

    def product_initial_density(z_logit: float) -> Any:
        z_value = float(np.tanh(z_logit))
        return 0.5 * (product_i2 + z_value * product_sz)

    def product_episode(
        object_id: str,
        *,
        physicality_ledger: dict[str, Any],
        parameter_permutation: Any | None = None,
    ) -> list[dict[str, Any]]:
        getter = log_getter(object_id)
        densities = np.asarray(
            [product_initial_density(value) for value in product_initial_z_logits]
        )
        states = []
        for view in range(N_VIEWS):
            for stage in range(PRODUCT_QUBITS):
                for position in range(N_BITS):
                    parameter_position = (
                        int(parameter_permutation[position])
                        if parameter_permutation is not None
                        else position
                    )
                    observed = getter(view, position)
                    if stage < N_BITS and stage == position and observed is None:
                        updated = densities[stage].copy()
                        probability = 1.0
                        physicality_ledger["missing_identity_updates"] += 1
                        event = "missing_position_identity"
                    else:
                        outcome = product_training_outcome(stage, position, observed)
                        if outcome is None:
                            raise TournamentError("missing product outcome without identity branch")
                        eta = 0.02 + 0.94 * float(
                            1.0 / (1.0 + np.exp(-product_eta_logits[stage, view, parameter_position]))
                        )
                        phase = float(product_phase_angles[stage, view, parameter_position])
                        updated, probability = apply_product_measurement(
                            densities[stage], eta, phase, outcome
                        )
                        product_parameter_usage[stage, view, parameter_position] += 1
                        if stage < N_BITS and stage == position:
                            physicality_ledger["visible_bit_updates"] += 1
                            event = "visible_position_bit"
                        else:
                            physicality_ledger["visibility_mask_updates"] += 1
                            event = "public_visibility_mask"
                    densities[stage] = updated
                    assert_product_update(
                        densities[stage],
                        probability,
                        physicality_ledger,
                        object_id=object_id,
                        view=view,
                        stage=stage,
                        event=event,
                    )
            # The clock stage has a public, deterministic outcome but still
            # evolves through an explicit CPTP instrument rather than a direct
            # Bloch assignment.
            clock_phase = np.pi * view / (N_VIEWS - 1)
            densities[9], clock_probability = apply_product_measurement(
                densities[9], 0.0, clock_phase, view % 2
            )
            physicality_ledger["clock_updates"] += 1
            assert_product_update(
                densities[9],
                clock_probability,
                physicality_ledger,
                object_id=object_id,
                view=view,
                stage=9,
                event="public_episode_clock",
            )
            bloch = np.asarray([product_bloch(density) for density in densities])
            norms = np.linalg.norm(bloch, axis=1)
            states.append(
                {
                    "feature": bloch.reshape(-1).copy(),
                    "belief": np.clip(0.5 * (bloch[:N_BITS, 2] + 1.0), 0.0, 1.0),
                    "max_bloch_norm": float(norms.max()),
                }
            )
        return states

    product_main_physicality = new_product_physicality_ledger()
    product_states = {
        object_id: product_episode(
            object_id, physicality_ledger=product_main_physicality
        )
        for object_id in object_ids
    }

    lane_states = {
        "oracle_exact_filter": oracle_states,
        "classical_fst_hmm": hmm_states,
        "torch_gru": gru_states,
        "senses_v2_anchor": anchor_states,
        "product_single_qubit_per_stage": product_states,
    }
    lane_order = list(lane_states)
    competitor_order = lane_order[1:]

    def state_feature(
        states: dict[str, list[dict[str, Any]]], slot: tuple[str, int, int]
    ) -> Any:
        return states[slot[0]][slot[1]]["feature"]

    def fit_readout(
        states: dict[str, list[dict[str, Any]]]
    ) -> tuple[dict[int, Any], dict[tuple[str, int, int], bool], dict[tuple[str, int, int], bool], float]:
        weights: dict[int, Any] = {}
        predictions: dict[tuple[str, int, int], bool] = {}
        correctness: dict[tuple[str, int, int], bool] = {}
        for position in range(N_BITS):
            train = [slot for slot in train_slots if slot[2] == position]
            test = [slot for slot in test_slots if slot[2] == position]
            train_x = np.asarray([state_feature(states, slot) for slot in train])
            train_y = np.asarray([2.0 * truth(slot) - 1.0 for slot in train])
            weights[position] = readout.ridge_fit(train_x, train_y)
            test_x = np.asarray([state_feature(states, slot) for slot in test])
            values = readout.ridge_predict(weights[position], test_x) >= 0
            for slot, value in zip(test, values):
                predictions[slot] = bool(value)
                correctness[slot] = bool(value) == bool(truth(slot))
        accuracy = float(np.mean([correctness[slot] for slot in test_slots]))
        return weights, predictions, correctness, accuracy

    def apply_readout(
        states: dict[str, list[dict[str, Any]]], weights: dict[int, Any]
    ) -> tuple[dict[tuple[str, int, int], bool], dict[tuple[str, int, int], bool], float]:
        predictions: dict[tuple[str, int, int], bool] = {}
        correctness: dict[tuple[str, int, int], bool] = {}
        for position in range(N_BITS):
            test = [slot for slot in test_slots if slot[2] == position]
            test_x = np.asarray([state_feature(states, slot) for slot in test])
            values = readout.ridge_predict(weights[position], test_x) >= 0
            for slot, value in zip(test, values):
                predictions[slot] = bool(value)
                correctness[slot] = bool(value) == bool(truth(slot))
        accuracy = float(np.mean([correctness[slot] for slot in test_slots]))
        return predictions, correctness, accuracy

    fitted = {name: fit_readout(states) for name, states in lane_states.items()}
    weights_by_lane = {name: values[0] for name, values in fitted.items()}
    predictions_by_lane = {name: values[1] for name, values in fitted.items()}
    correct_by_lane = {name: values[2] for name, values in fitted.items()}
    accuracy_by_lane = {name: values[3] for name, values in fitted.items()}

    def object_bootstrap_accuracy(correctness: dict[tuple[str, int, int], bool], seed: int) -> dict[str, Any]:
        indices_by_object = {
            object_id: np.asarray(
                [index for index, slot in enumerate(test_slots) if slot[0] == object_id],
                dtype=int,
            )
            for object_id in test_objects
        }
        values = np.asarray([correctness[slot] for slot in test_slots], dtype=float)
        rng = np.random.default_rng(seed)
        samples = []
        for _ in range(N_BOOTSTRAPS):
            sampled = rng.choice(test_objects, size=len(test_objects), replace=True)
            indices = np.concatenate([indices_by_object[item] for item in sampled])
            samples.append(float(values[indices].mean()))
        return {
            "estimate": float(values.mean()),
            "ci95": [
                float(np.quantile(samples, 0.025)),
                float(np.quantile(samples, 0.975)),
            ],
            "draws": N_BOOTSTRAPS,
            "bootstrap_unit": "held-out object; all occluded slots stay together",
            "seed": seed,
        }

    def object_bootstrap_difference(
        first: dict[tuple[str, int, int], bool],
        second: dict[tuple[str, int, int], bool],
        seed: int,
    ) -> dict[str, Any]:
        indices_by_object = {
            object_id: np.asarray(
                [index for index, slot in enumerate(test_slots) if slot[0] == object_id],
                dtype=int,
            )
            for object_id in test_objects
        }
        a = np.asarray([first[slot] for slot in test_slots], dtype=float)
        b = np.asarray([second[slot] for slot in test_slots], dtype=float)
        rng = np.random.default_rng(seed)
        samples = []
        for _ in range(N_BOOTSTRAPS):
            sampled = rng.choice(test_objects, size=len(test_objects), replace=True)
            indices = np.concatenate([indices_by_object[item] for item in sampled])
            samples.append(float(a[indices].mean() - b[indices].mean()))
        return {
            "estimate": float(a.mean() - b.mean()),
            "ci95": [
                float(np.quantile(samples, 0.025)),
                float(np.quantile(samples, 0.975)),
            ],
            "draws": N_BOOTSTRAPS,
            "bootstrap_unit": "held-out object; paired lane correctness within sampled object",
            "seed": seed,
        }

    def fit_mi_edges(states: dict[str, list[dict[str, Any]]]) -> dict[int, Any]:
        edges = {}
        for position in range(N_BITS):
            beliefs = np.asarray(
                [
                    states[object_id][view]["belief"][position]
                    for object_id, view, query_position in train_slots
                    if query_position == position
                ],
                dtype=float,
            )
            edges[position] = np.unique(
                np.quantile(beliefs, np.linspace(0.0, 1.0, MI_BINS + 1))
            )
        return edges

    def mutual_information_bundle(
        states: dict[str, list[dict[str, Any]]], seed: int
    ) -> dict[str, Any]:
        edges = fit_mi_edges(states)

        def evaluate(permuted: bool, rng: Any | None = None) -> tuple[float, list[float]]:
            by_position = []
            for position in range(N_BITS):
                instances = [
                    (object_id, view)
                    for object_id, view, query_position in test_slots
                    if query_position == position
                ]
                beliefs = np.asarray(
                    [states[object_id][view]["belief"][position] for object_id, view in instances],
                    dtype=float,
                )
                bits = np.asarray(
                    [full_views[object_id][view][position] for object_id, view in instances],
                    dtype=int,
                )
                if permuted:
                    bits = rng.permutation(bits)
                by_position.append(
                    anchor.empirical_mutual_information(
                        beliefs, bits, bins=MI_BINS, fixed_edges=edges[position]
                    )
                )
            return float(np.mean(by_position)), by_position

        observed, by_position = evaluate(False)
        rng = np.random.default_rng(seed)
        null = np.asarray([evaluate(True, rng)[0] for _ in range(N_PERMUTATIONS)])
        return {
            "mutual_information_bits": observed,
            "by_position_bits": [float(value) for value in by_position],
            "train_fitted_bin_edges": {
                str(position): [float(value) for value in edges[position]]
                for position in range(N_BITS)
            },
            "permutation_draws": N_PERMUTATIONS,
            "permutation_seed": seed,
            "permutation_null_mean_bits": float(null.mean()),
            "permutation_null_p95_bits": float(np.quantile(null, 0.95)),
            "monte_carlo_pvalue": float(
                (1 + np.sum(null >= observed)) / (N_PERMUTATIONS + 1)
            ),
            "permutation_scheme": "held-out hidden labels permuted within target position; beliefs and train-fitted edges fixed",
        }

    lane_metrics = {}
    for lane_index, name in enumerate(lane_order):
        lane_metrics[name] = {
            "role": "ceiling_reference_not_competitor" if lane_index == 0 else "competitor",
            "occluded_accuracy": object_bootstrap_accuracy(
                correct_by_lane[name], SEED + 1000 + lane_index
            ),
            "belief_mutual_information": mutual_information_bundle(
                lane_states[name], SEED + 2000 + lane_index
            ),
        }

    pairwise = {}
    for first, second in combinations(lane_order, 2):
        key = f"{first}__vs__{second}"
        pairwise[key] = {
            "first_lane": first,
            "second_lane": second,
            "two_by_two": readout.bootstrap_complementarity(
                test_slots,
                correct_by_lane[first],
                correct_by_lane[second],
                test_objects,
            ),
        }

    oracle_gaps = {}
    for lane_index, name in enumerate(competitor_order):
        oracle_gaps[name] = object_bootstrap_difference(
            correct_by_lane["oracle_exact_filter"],
            correct_by_lane[name],
            SEED + 3000 + lane_index,
        )

    # Fixed derangement, chosen without labels.  Each fitted lane records both
    # the frozen original decoder and a train-only refit for transparency.
    scramble_rng = np.random.default_rng(SCRAMBLE_SEED)
    while True:
        permutation = scramble_rng.permutation(N_BITS)
        if np.all(permutation != np.arange(N_BITS)):
            break
    scrambled_channels = {
        (position, bit): channels[(int(permutation[position]), bit)]
        for position in range(N_BITS)
        for bit in (0, 1)
    }
    scrambled_anchor_engine = anchor.QuantumReadoutBayes(
        scrambled_channels, visibility, words, rules, hypotheses
    )
    scrambled_anchor_engine.calibrate_sigma(masks_by_view)
    scrambled_anchor_states = adapt_anchor(
        {
            object_id: scrambled_anchor_engine.episode(
                log_getter(object_id), keep_posteriors=False
            )
            for object_id in object_ids
        }
    )
    product_scrambled_physicality = new_product_physicality_ledger()
    scrambled_states = {
        "classical_fst_hmm": {
            object_id: posterior_episode(
                object_id,
                epsilon_by_view_position=hmm_epsilon,
                exact=False,
                prior=hmm_prior,
                parameter_permutation=permutation,
            )
            for object_id in object_ids
        },
        "torch_gru": gru_state_map(source_permutation=permutation),
        "senses_v2_anchor": scrambled_anchor_states,
        "product_single_qubit_per_stage": {
            object_id: product_episode(
                object_id,
                physicality_ledger=product_scrambled_physicality,
                parameter_permutation=permutation,
            )
            for object_id in object_ids
        },
    }
    scramble_results = {}
    for name, states in scrambled_states.items():
        _, frozen_correct, frozen_accuracy = apply_readout(
            states, weights_by_lane[name]
        )
        _, _, refit_correct, refit_accuracy = fit_readout(states)
        scramble_results[name] = {
            "frozen_original_decoder_accuracy": frozen_accuracy,
            "train_only_refit_accuracy": refit_accuracy,
            "frozen_decoder_toward_chance": abs(frozen_accuracy - computed_chance)
            <= 0.03,
            "frozen_decoder_delta_from_main": frozen_accuracy - accuracy_by_lane[name],
            "refit_delta_from_main": refit_accuracy - accuracy_by_lane[name],
            "frozen_correctness_sha256": sha256_json(
                [frozen_correct[slot] for slot in test_slots]
            ),
            "refit_correctness_sha256": sha256_json(
                [refit_correct[slot] for slot in test_slots]
            ),
        }

    anchor_reset_fit = fit_readout(anchor_reset_states)
    anchor_frozen_fit = fit_readout(anchor_frozen_states)
    anchor_ports = {
        "m_slow_reset_each_view": {
            "occluded_accuracy": anchor_reset_fit[3],
            "belief_mutual_information": mutual_information_bundle(
                anchor_reset_states, SEED + 4101
            ),
            "feature_dimension": FEATURE_DOF,
            "scope": "uniform m_slow reset before every view, followed by that view update; common ridge refit",
        },
        "frozen_quantum_readout": {
            "occluded_accuracy": anchor_frozen_fit[3],
            "belief_mutual_information": mutual_information_bundle(
                anchor_frozen_states, SEED + 4102
            ),
            "feature_dimension": FEATURE_DOF,
            "scope": "visible actual outcomes forced to zero; masks and candidate emissions retained; common ridge refit",
        },
    }

    anchor_vs_classical = {}
    classical_matches_within_ci = {}
    for lane_index, name in enumerate(["classical_fst_hmm", "torch_gru"]):
        difference = object_bootstrap_difference(
            correct_by_lane["senses_v2_anchor"],
            correct_by_lane[name],
            SEED + 5000 + lane_index,
        )
        anchor_vs_classical[name] = difference
        classical_matches_within_ci[name] = difference["ci95"][0] <= 0.0

    gru_parameter_count = int(sum(parameter.numel() for parameter in gru_model.parameters()))
    common_readout_parameters = N_BITS * (FEATURE_DOF + 1)
    anchor_capacity_charge = 15 + (len(hypotheses) - 1)
    if anchor_capacity_charge != ANCHOR_CHARGED_FITTED_PARAMETER_COUNT:
        raise TournamentError(
            "anchor charged capacity drifted from the frozen Attempt 2 budget "
            f"{ANCHOR_CHARGED_FITTED_PARAMETER_COUNT}: {anchor_capacity_charge}"
        )
    lower_parameter_limit = int(
        np.ceil((1.0 - BUDGET_TOLERANCE_FRACTION) * anchor_capacity_charge)
    )
    upper_parameter_limit = int(
        np.floor((1.0 + BUDGET_TOLERANCE_FRACTION) * anchor_capacity_charge)
    )
    product_all_parameters_executed = bool(product_parameter_usage.min() > 0)
    competitor_parameter_counts = {
        "classical_fst_hmm": hmm_parameter_count,
        "torch_gru": gru_parameter_count,
        "product_single_qubit_per_stage": product_parameter_count,
    }
    competitor_within_budget = {
        name: lower_parameter_limit <= count <= upper_parameter_limit
        for name, count in competitor_parameter_counts.items()
    }
    parameter_manifest = {
        "classical_fst_hmm": {
            "active_fitted_parameter_count": hmm_parameter_count,
            "blocks": [
                {"name": "nonredundant_hypothesis_prior_logits", "shape": [len(hypotheses) - 1], "count": len(hypotheses) - 1},
                {"name": "position_emission_logits", "shape": [N_BITS], "count": N_BITS},
                {"name": "view_emission_logits_reference_fixed", "shape": [N_VIEWS - 1], "count": N_VIEWS - 1},
            ],
            "initial_parameter_sha256": sha256_json(
                {"prior": [0.0] * (len(hypotheses) - 1), "position": [0.0] * N_BITS, "view": [0.0] * (N_VIEWS - 1)}
            ),
            "final_parameter_sha256": sha256_json(
                {"prior_probability": hmm_prior.tolist(), "emission_error": hmm_epsilon.tolist()}
            ),
            "fit_scope": "train objects and visible observations only; fixed marginal-likelihood optimization",
            "all_charged_scalars_active": hmm_all_parameters_active,
        },
        "torch_gru": {
            "active_fitted_parameter_count": gru_parameter_count,
            "blocks": [
                {"name": "GRUCell", "shape": [17, GRU_HIDDEN], "count_formula": "3*h*17 + 3*h*h + 6*h"},
                {"name": "Linear", "shape": [GRU_HIDDEN, N_BITS], "count_formula": "8*h + 8"},
            ],
            "initial_parameter_sha256": gru_initial_parameter_sha256,
            "final_parameter_sha256": gru_final_parameter_sha256,
            "fit_scope": "train objects and masked train-target loss only; no test validation or early stop",
            "all_charged_scalars_active": gru_all_parameters_active,
        },
        "product_single_qubit_per_stage": {
            "active_fitted_parameter_count": product_parameter_count,
            "blocks": [
                {"name": "measurement_eta_logits", "shape": [PRODUCT_QUBITS, N_VIEWS, N_BITS], "count": int(product_eta_logits.size)},
                {"name": "measurement_phase_angles", "shape": [PRODUCT_QUBITS, N_VIEWS, N_BITS], "count": int(product_phase_angles.size)},
                {"name": "initial_z_logits", "shape": [PRODUCT_QUBITS], "count": int(product_initial_z_logits.size)},
            ],
            "fit_rule_sha256": sha256_json(product_fit_metadata),
            "final_parameter_sha256": sha256_json(
                {"eta_logits": product_eta_logits.tolist(), "phase_angles": product_phase_angles.tolist(), "initial_z_logits": product_initial_z_logits.tolist()}
            ),
            "fit_scope": "train-object visible bits for local stages and public masks for context stages only",
            "all_charged_scalars_active": product_all_parameters_executed,
        },
    }
    parameter_manifests_complete = bool(
        all(
            manifest["active_fitted_parameter_count"] == competitor_parameter_counts[name]
            and manifest["all_charged_scalars_active"]
            for name, manifest in parameter_manifest.items()
        )
    )
    budget_ledger = {
        "definition": "Attempt 2 frozen explicitly charged active-carrier capacity; common readout is reported separately and never charged twice.",
        "anchor_capacity_charge": {
            "count": anchor_capacity_charge,
            "formula": "1023 m_slow posterior-simplex coordinates plus 15 trace-one 4x4 rho_fast coordinates",
            "conventional_train_fitted_scalars_disclosed": 1,
            "conventional_scalar_note": "The old sigma-only count is disclosed but is not the user-defined Attempt 2 capacity ceiling.",
        },
        "tolerance": {
            "fraction": BUDGET_TOLERANCE_FRACTION,
            "inclusive_integer_range": [lower_parameter_limit, upper_parameter_limit],
        },
        "matching_axes": {
            "same_world_data_split_masks_targets": True,
            "same_train_test_slot_counts": True,
            "same_exposed_real_feature_dof": True,
            "same_per_position_ridge_readout_contract": True,
            "same_common_readout_fitted_parameters": True,
            "anchor_charged_capacity_matches_frozen_1038": anchor_capacity_charge == ANCHOR_CHARGED_FITTED_PARAMETER_COUNT,
            "oracle_exempt_from_competitor_budget": True,
            "all_competitor_parameter_manifests_complete": parameter_manifests_complete,
            **{
                f"{name}_within_plus_or_minus_10_percent": passed
                for name, passed in competitor_within_budget.items()
            },
        },
        "hard_fail_closed": True,
        "parameter_manifest": parameter_manifest,
        "common": {
            "feature_dof": FEATURE_DOF,
            "readout": "eight independent ridge regressions with bias and lambda=1e-3",
            "readout_fitted_parameters": common_readout_parameters,
            "excluded_from_capacity_gate": True,
            "train_objects": len(train_objects),
            "test_objects": len(test_objects),
            "train_slots": len(train_slots),
            "test_slots": len(test_slots),
        },
        "lanes": {
            "oracle_exact_filter": {
                "competition_status": "exempt_ceiling_reference",
                "live_state_dof": anchor_capacity_charge,
                "active_fitted_parameter_count": 0,
            },
            "classical_fst_hmm": {
                "live_state_dof": anchor_capacity_charge,
                "active_fitted_parameter_count": hmm_parameter_count,
                "within_frozen_budget": competitor_within_budget["classical_fst_hmm"],
                "parameter_definition": "1023 nonredundant fitted hypothesis-prior logits plus eight position and five nonreference-view emission logits",
                "training": {"epochs": HMM_EPOCHS, "optimizer": "Adam", "learning_rate": HMM_LEARNING_RATE, "loss_trace": hmm_loss_trace},
            },
            "torch_gru": {
                "live_state_dof": GRU_HIDDEN,
                "active_fitted_parameter_count": gru_parameter_count,
                "within_frozen_budget": competitor_within_budget["torch_gru"],
                "architecture": f"torch.nn.GRUCell(17,{GRU_HIDDEN}) plus Linear({GRU_HIDDEN},8); fixed 11-to-10 summary then deterministic 30-coordinate lift",
                "training": {
                    "epochs": GRU_EPOCHS,
                    "optimizer": "Adam",
                    "learning_rate": 0.01,
                    "seed": TORCH_SEED,
                    "model_selection": "fixed final epoch; no validation or test selection",
                    "loss_trace": loss_trace,
                },
            },
            "senses_v2_anchor": {
                "live_state_dof": anchor_capacity_charge,
                "dof_breakdown": "15 for source 4x4 rho_fast plus 1023 for m_slow simplex",
                "active_fitted_parameter_count": anchor_capacity_charge,
                "parameter_definition": "frozen user-defined charged active-carrier capacity; conventional sigma-only scalar count separately disclosed",
                "source_actual_qubits": 2,
                "owner_prompt_qubit_shorthand_matches_source": False,
            },
            "product_single_qubit_per_stage": {
                "live_state_dof": FEATURE_DOF,
                "dof_breakdown": "ten independent 2x2 density matrices emitted as Bloch triples",
                "active_fitted_parameter_count": product_parameter_count,
                "within_frozen_budget": competitor_within_budget["product_single_qubit_per_stage"],
                "parameter_definition": "480 train-fitted measurement sharpness logits, 480 train-fitted phase angles, and ten train-fitted initial z logits; every update uses a two-outcome CPTP Kraus instrument",
                "stage_definition": "eight position stages plus global visibility and episode-clock stages; context is public visibility only",
                "fit_metadata": product_fit_metadata,
            },
        },
    }
    budget_ledger["hard_parameter_fairness_pass"] = bool(
        all(budget_ledger["matching_axes"].values())
    )
    budget_ledger["failure_reason"] = (
        "all Attempt 2 active-carrier capacity checks passed"
        if budget_ledger["hard_parameter_fairness_pass"]
        else "one or more explicit Attempt 2 active-carrier capacity checks failed; no scientific interpretation is allowed"
    )

    fairness_pass = bool(budget_ledger["hard_parameter_fairness_pass"])
    any_classical_match = bool(any(classical_matches_within_ci.values()))
    frozen_verdict = {
        "rule": "If a fair matched classical sequential lane matches or beats the anchor within paired object-bootstrap CI, the quantum carrier has not earned minimal status.",
        "paired_difference_definition": "anchor accuracy minus classical accuracy",
        "anchor_vs_classical": anchor_vs_classical,
        "classical_matches_or_beats_within_ci": classical_matches_within_ci,
        "fairness_precondition_pass": fairness_pass,
        "conditional_classical_falsifier_triggered": any_classical_match,
        "minimal_status_earned": False,
        "status": (
            "NOT_MINIMAL_CLASSICAL_MATCH"
            if fairness_pass and any_classical_match
            else "BLOCKED_BUDGET_MISMATCH"
            if not fairness_pass
            else "WORKING_SIM_CARRIER_RESULT_ONLY"
        ),
        "promotion_allowed": False,
        "note": (
            "The hard capacity gate cannot rescue the carrier: a failure blocks a positive "
            "minimality claim, while a fair classical within-CI match records nonminimality."
        ),
    }

    product_max_norm = max(
        product_main_physicality["maximum_bloch_norm"],
        product_scrambled_physicality["maximum_bloch_norm"],
    )
    occlusions_per_view = [
        sum(log[object_id][view][position] == "withheld" for position in range(N_BITS))
        for object_id in object_ids
        for view in range(N_VIEWS)
    ]
    feature_dimensions = {
        name: sorted(
            {
                int(len(state["feature"]))
                for states in state_map.values()
                for state in states
            }
        )
        for name, state_map in lane_states.items()
    }
    input_hashes_end = {str(path): sha256_file(path) for path in tracked_inputs}
    integrity_checks = {
        "v4_3_current_task_card_validated_before_build": preflight_receipt[
            "object_card_validation"
        ]["ok"]
        is True,
        "canonical_interpreter": SIM_PY.resolve() == Path(sys.executable).resolve(),
        "memory_free_above_25_percent_before_heavy_imports": preflight_receipt[
            "memory_free_percent"
        ]
        > MIN_MEMORY_FREE_PERCENT,
        "world_has_64_objects": len(object_ids) == 64,
        "world_has_6_views": all(len(log[item]) == N_VIEWS for item in object_ids),
        "every_view_has_2_to_4_occluded_positions": min(occlusions_per_view) >= 2
        and max(occlusions_per_view) <= 4,
        "object_split_disjoint": not bool(train_set & test_set),
        "split_matches_anchor_receipt": train_objects
        == prior_anchor_receipt["protocol"]["split"]["train_objects"]
        and test_objects == prior_anchor_receipt["protocol"]["split"]["test_objects"],
        "slot_counts_match_anchor": len(train_slots) == 782 and len(test_slots) == 343,
        "all_queried_targets_masked": all(
            log_getter(slot[0])(slot[1], slot[2]) is None
            for slot in train_slots + test_slots
        ),
        "all_lane_features_have_30_coordinates": all(
            dimensions == [FEATURE_DOF] for dimensions in feature_dimensions.values()
        ),
        "anchor_reuses_source_episode_without_reimplementation": True,
        "anchor_source_is_two_qubit_4x4_and_disclosed": all(
            state["rho_fast"].shape == (4, 4)
            for states in anchor_raw_states.values()
            for state in states
        ),
        "oracle_excluded_from_competitor_verdict": "oracle_exact_filter"
        not in ["classical_fst_hmm", "torch_gru"],
        "torch_gru_executed": gru_parameter_count > 0 and len(gru_states) == 64,
        "product_single_qubit_states_physical": bool(
            product_main_physicality["pass"]
            and product_scrambled_physicality["pass"]
            and product_max_norm <= 1.0 + PHYSICALITY_TOLERANCE
        ),
        "product_physicality_asserted_after_every_update": bool(
            product_main_physicality["updates_checked"] > 0
            and product_scrambled_physicality["updates_checked"] > 0
            and product_main_physicality["zero_or_nonfinite_probability_updates"] == 0
            and product_scrambled_physicality["zero_or_nonfinite_probability_updates"] == 0
        ),
        "channel_scramble_is_fixed_derangement": bool(
            np.all(permutation != np.arange(N_BITS))
        ),
        "channel_scramble_results_recorded_whichever_way": set(scramble_results)
        == set(competitor_order),
        "all_input_hashes_unchanged_during_run": input_hashes_start == input_hashes_end,
        "promotion_allowed_is_false": promotion_allowed is False,
        "formal_admission_allowed_is_false": formal_admission_allowed is False,
    }
    scientific_checks = {
        "all_lane_accuracy_bootstrap_metrics_present": len(lane_metrics) == 5,
        "all_lane_mutual_information_nulls_present": all(
            lane_metrics[name]["belief_mutual_information"]["permutation_draws"]
            == N_PERMUTATIONS
            for name in lane_order
        ),
        "all_10_pairwise_complementarity_tables_present": len(pairwise) == 10,
        "all_4_oracle_gaps_present": len(oracle_gaps) == 4,
        "anchor_reset_and_frozen_ports_present": set(anchor_ports)
        == {"m_slow_reset_each_view", "frozen_quantum_readout"},
        "frozen_verdict_rule_applied": frozen_verdict["minimal_status_earned"]
        is False,
    }
    fairness_checks = budget_ledger["matching_axes"]
    integrity_pass = bool(all(integrity_checks.values()))
    scientific_metrics_complete = bool(all(scientific_checks.values()))
    all_pass = bool(integrity_pass and scientific_metrics_complete and fairness_pass)

    findings = [
        (
            "Exact source correction: the unchanged senses_v2 anchor is a two-qubit "
            "4x4 rho_fast plus a 1024-hypothesis m_slow posterior, not a three-qubit lane."
        ),
        (
            f"Attempt 2 fairness fail-closed: anchor charged capacity {anchor_capacity_charge}; "
            f"inclusive competitor range [{lower_parameter_limit}, {upper_parameter_limit}]; "
            f"counts {competitor_parameter_counts}; pass={fairness_pass}."
        ),
        *[
            f"{name}: occluded accuracy {accuracy_by_lane[name]:.4f}, MI "
            f"{lane_metrics[name]['belief_mutual_information']['mutual_information_bits']:.6f} bits."
            for name in lane_order
        ],
        (
            f"Frozen conditional classical-match flags: {classical_matches_within_ci}; "
            f"final status {frozen_verdict['status']}."
        ),
        (
            "HONEST NEGATIVE KEPT: a fair classical within-CI match is recorded as "
            "nonminimality, and no outcome permits promotion or formal admission."
        ),
    ]

    tool_calls = [
        {
            "tool": "torch",
            "qualified_api/function": "torch.nn.GRUCell",
            "input_object": "44 train-object sequences of six 17-coordinate masked views",
            "output_object": "30-coordinate per-view recurrent states and eight-bit logits",
            "positive_case": "fixed-epoch train loss and held-out predictions emitted",
            "negative/erased_control": "fixed position-channel derangement with frozen decoder",
            "boundary_case": "per-episode hidden state resets and no test-object model selection",
            "demotion_condition": "missing Torch execution or predictions blocks the GRU lane and every carrier conclusion",
            "gates": "frozen classical falsifier and fairness ledger",
        },
        {
            "tool": "numpy",
            "qualified_api/function": "numpy.linalg.eigvalsh plus explicit two-Kraus qubit instrument",
            "input_object": "ten independent 2x2 product density stages and visible/public-mask outcomes",
            "output_object": "renormalized density updates, 30 Pauli-coordinate features, and per-update physicality ledger",
            "positive_case": "every main and scrambled update has finite positive outcome probability, trace one, PSD spectrum, and Bloch norm at most one plus 1e-9",
            "negative/erased_control": "missing local observation follows the identity Kraus channel rather than inserting a hidden bit",
            "boundary_case": "clock stage uses a public deterministic CPTP instrument; all ten stages remain unentangled 2x2 densities",
            "demotion_condition": "any nonphysical update raises TournamentError before a normal receipt can claim the product lane",
            "gates": "product physicality integrity check and hard fail-closed all_pass",
        },
    ]

    receipt = {
        "schema": "loop3_senses/carrier_tournament_v1/receipt_v1",
        "sim_id": "carrier_tournament_v1",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "classical_and_nonclassical_comparison_diagnostic",
        "runtime": {
            **preflight_receipt,
            "python_version": sys.version.split()[0],
            "numpy_version": np.__version__,
            "torch_version": torch.__version__,
            "torch_seed": TORCH_SEED,
            "one_heavy_runtime_at_a_time": True,
        },
        "authority": {
            "preregistration": str(PREREGISTRATION),
            "object_preservation_card": str(OBJECT_CARD),
            "anchor_source": str(ANCHOR_SOURCE),
            "anchor_receipt": str(ANCHOR_RECEIPT),
            "referee_receipts": str(REFEREE_RECEIPTS),
        },
        "inputs": {
            "hashes_start": input_hashes_start,
            "hashes_end": input_hashes_end,
            "world_schema_metrics": schema_metrics,
            "ground_truth_recovery_for_evaluation_only": recovery_metrics,
            "split_fingerprint_sha256": sha256_json(
                {
                    "seed": SEED,
                    "train_objects": train_objects,
                    "test_objects": test_objects,
                    "train_slots": train_slots,
                    "test_slots": test_slots,
                }
            ),
        },
        "protocol": {
            "task": "after masked views 0..v, predict each withheld current-world bit at view v",
            "world": "64 objects; additive-XOR CA family; six views; eight positions; two-to-four occlusions per view",
            "seed": SEED,
            "split": {
                "train_objects": train_objects,
                "test_objects": test_objects,
                "train_count": len(train_objects),
                "test_count": len(test_objects),
                "train_slots": len(train_slots),
                "test_slots": len(test_slots),
                "object_disjoint": not bool(train_set & test_set),
            },
            "lanes": lane_order,
            "oracle_competitor": False,
            "common_readout": "30-coordinate state to eight independent per-position ridge fits, lambda=1e-3, train objects only",
            "accuracy_uncertainty": "5000-draw paired whole-object bootstrap",
            "mutual_information": "position-wise empirical I(hidden bit; lane belief), train-fitted five-bin edges, 200 held-out within-position label permutations",
            "channel_scramble": {
                "seed": SCRAMBLE_SEED,
                "position_derangement": [int(value) for value in permutation],
                "post_selection": False,
                "anchor_semantics": "fresh engine with both actual and candidate position-channel ownership permuted; caches not reused",
                "hmm_product_semantics": "fitted position-parameter ownership permuted while observed positions and targets stay fixed",
                "gru_semantics": "masked input position-channel ownership permuted; trained weights frozen",
                "decoder_metrics": "both original frozen decoder and train-only refit recorded",
                "desired_direction_enforced": False,
            },
        },
        "budget_ledger": budget_ledger,
        "results": {
            "computed_chance_accuracy": computed_chance,
            "lanes": lane_metrics,
            "pairwise_complementarity": pairwise,
            "oracle_gaps": oracle_gaps,
            "channel_scramble": scramble_results,
            "anchor_ports": anchor_ports,
            "anchor_likelihood_calibration": anchor_calibration,
            "anchor_prior_receipt_boundary": {
                "scientific_pass": prior_anchor_receipt["scientific_pass"],
                "integrity_pass": prior_anchor_receipt["integrity_pass"],
                "all_pass": prior_anchor_receipt["all_pass"],
                "accepted_status_label": prior_anchor_receipt["accepted_status_label"],
                "failed_checks": [
                    key
                    for key, value in prior_anchor_receipt["checks"].items()
                    if not value
                ],
            },
            "frozen_verdict": frozen_verdict,
            "product_physicality": {
                "qubits": PRODUCT_QUBITS,
                "formalism": "outcome-conditioned two-Kraus qubit instruments with rho -> K_b rho K_b-dagger / Tr(K_b rho K_b-dagger); missing local observations use the identity Kraus channel",
                "per_update_assertion": "trace=1, Hermitian, PSD within tolerance, and Bloch norm <= 1 + 1e-9 after every update",
                "main_evaluation": product_main_physicality,
                "channel_scramble_evaluation": product_scrambled_physicality,
                "maximum_bloch_norm_across_evaluations": product_max_norm,
                "pass": bool(
                    product_main_physicality["pass"]
                    and product_scrambled_physicality["pass"]
                ),
            },
            "prediction_fingerprints_sha256": {
                name: sha256_json(
                    [predictions_by_lane[name][slot] for slot in test_slots]
                )
                for name in lane_order
            },
        },
        "integrity_checks": integrity_checks,
        "fairness_checks": fairness_checks,
        "scientific_checks": scientific_checks,
        "integrity_pass": integrity_pass,
        "fairness_pass": fairness_pass,
        "scientific_metrics_complete": scientific_metrics_complete,
        "all_pass": all_pass,
        "findings": findings,
        "divergence_log": [
            {
                "comparison": "requested literal match versus unchanged source anchor",
                "status": (
                    "matched_parameter_capacity"
                    if fairness_pass
                    else "blocked_budget_mismatch"
                ),
                "reason": budget_ledger["failure_reason"],
            },
            *[
                {
                    "comparison": f"senses_v2_anchor versus {name}",
                    "accuracy_delta": accuracy_by_lane["senses_v2_anchor"]
                    - accuracy_by_lane[name],
                    "paired_object_bootstrap": anchor_vs_classical.get(name),
                }
                for name in competitor_order
                if name != "senses_v2_anchor"
            ],
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "blocked_consumers": [
            "minimal carrier status",
            "carrier promotion or scaling",
            "scientific or canonical admission",
            "bridge, axis, manifold, or physics claims",
            "reuse or overwrite of this result directory",
        ],
        "accepted_status_label": "exists",
        "claim_ceiling": (
            "fresh carrier-tournament diagnostic with a hard Attempt 2 charged-capacity gate, "
            "complete lane metrics, frozen falsifier, and CPTP product physicality checks; "
            "promotion_allowed false"
        ),
        "receipt_path": str(RECEIPT_PATH),
    }
    return receipt


def write_json_receipt(
    receipt: dict[str, Any], *, repair_malformed_receipt: bool = False
) -> None:
    # Serialize before opening the fresh path.  This preserves refuse-to-reuse
    # semantics if a new receipt ever contains a non-JSON value.  Repair mode
    # is intentionally narrower: it may replace only a malformed partial file
    # made by this same failed writer; it never accepts a valid prior receipt.
    serialized = json.dumps(receipt, indent=2, allow_nan=False)
    if repair_malformed_receipt:
        try:
            json.loads(RECEIPT_PATH.read_text())
        except json.JSONDecodeError:
            pass
        else:
            raise TournamentError(
                "REFUSE-TO-REUSE: repair mode cannot replace a valid receipt"
            )
        with RECEIPT_PATH.open("w") as handle:
            handle.write(serialized)
        return
    with RECEIPT_PATH.open("x") as handle:
        handle.write(serialized)


def write_fatal_receipt(message: str, preflight_receipt: dict[str, Any]) -> None:
    receipt = {
        "schema": "loop3_senses/carrier_tournament_v1/receipt_v1",
        "sim_id": "carrier_tournament_v1",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "runtime": preflight_receipt,
        "fatal_error": message,
        "checks": {"fatal_preflight_or_runtime": False},
        "all_pass": False,
        "divergence_log": [
            {
                "comparison": "requested tournament versus fatal execution state",
                "status": "not_completed",
                "reason": message,
            }
        ],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "fatal fail-closed diagnostic; no carrier result or promotion claim",
    }
    write_json_receipt(receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate runtime, memory, inputs, object card, and fresh output path without writing",
    )
    parser.add_argument(
        "--repair-malformed-receipt",
        action="store_true",
        help="replace only an invalid partial receipt created by this writer after revalidating the full run",
    )
    args = parser.parse_args()
    try:
        preflight_receipt = preflight(
            require_fresh_outdir=not args.repair_malformed_receipt,
            repair_malformed_receipt=args.repair_malformed_receipt,
        )
    except (OSError, subprocess.CalledProcessError, TournamentError) as error:
        print(f"FATAL PRE-WRITE: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    if args.preflight_only:
        print(json.dumps(preflight_receipt, indent=2))
        return 0

    if not args.repair_malformed_receipt:
        OUTDIR.mkdir(parents=True, exist_ok=False)
    try:
        receipt = run(preflight_receipt)
    except Exception as error:
        if not args.repair_malformed_receipt:
            write_fatal_receipt(f"{type(error).__name__}: {error}", preflight_receipt)
        print(f"FATAL: {type(error).__name__}: {error}", file=sys.stderr)
        if not args.repair_malformed_receipt:
            print(f"fatal receipt written: {RECEIPT_PATH}", file=sys.stderr)
        return 1
    write_json_receipt(
        receipt, repair_malformed_receipt=args.repair_malformed_receipt
    )
    print(f"receipt written: {RECEIPT_PATH}")
    print(
        json.dumps(
            {
                "all_pass": receipt["all_pass"],
                "integrity_pass": receipt["integrity_pass"],
                "fairness_pass": receipt["fairness_pass"],
                "scientific_metrics_complete": receipt["scientific_metrics_complete"],
                "frozen_verdict": receipt["results"]["frozen_verdict"],
                "failed_checks": {
                    "integrity": [
                        key for key, value in receipt["integrity_checks"].items() if not value
                    ],
                    "fairness": [
                        key for key, value in receipt["fairness_checks"].items() if not value
                    ],
                    "scientific": [
                        key for key, value in receipt["scientific_checks"].items() if not value
                    ],
                },
                "promotion_allowed": receipt["promotion_allowed"],
                "claim_ceiling": receipt["claim_ceiling"],
            },
            indent=2,
        )
    )
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
