#!/usr/bin/env python3
from __future__ import annotations

from typing import Mapping


def _bool_gate_fraction(gates: Mapping[str, bool]) -> float:
    if not gates:
        return 0.0
    return float(sum(1.0 if value else 0.0 for value in gates.values()) / len(gates))


def build_constraint_family_profile(
    *,
    observational: float = 0.0,
    admissible: float = 0.0,
    stable: float = 0.0,
    entropy_conditioned: float = 0.0,
    topology_conditioned: float = 0.0,
) -> dict[str, float]:
    return {
        "observational": float(observational),
        "admissible": float(admissible),
        "stable": float(stable),
        "entropy_conditioned": float(entropy_conditioned),
        "topology_conditioned": float(topology_conditioned),
    }


def build_distinguishability_constraint(
    *,
    observational: bool,
    admissible: bool,
    stable: bool,
    entropy_conditioned: bool,
    topology_conditioned: bool,
    note: str,
    pass_threshold: float = 1.0,
    signals: Mapping[str, float] | None = None,
) -> dict[str, object]:
    gates = {
        "observational": bool(observational),
        "admissible": bool(admissible),
        "stable": bool(stable),
        "entropy_conditioned": bool(entropy_conditioned),
        "topology_conditioned": bool(topology_conditioned),
    }
    gate_fraction = _bool_gate_fraction(gates)
    normalized_signals = {} if signals is None else {str(k): float(v) for k, v in signals.items()}
    constraint_profile = build_constraint_family_profile(
        observational=float(normalized_signals.get("observational_signal", 0.0)),
        admissible=float(normalized_signals.get("admissibility_signal", 0.0)),
        stable=float(normalized_signals.get("stability_signal", 0.0)),
        entropy_conditioned=float(normalized_signals.get("entropy_signal", 0.0)),
        topology_conditioned=float(normalized_signals.get("topology_signal", 0.0)),
    )
    return {
        "type": "distinguishability_constraint",
        "pass": bool(gate_fraction >= float(pass_threshold)),
        "gate_fraction": gate_fraction,
        "pass_threshold": float(pass_threshold),
        "gates": gates,
        "signals": normalized_signals,
        "constraint_profile": constraint_profile,
        "note": note,
    }
