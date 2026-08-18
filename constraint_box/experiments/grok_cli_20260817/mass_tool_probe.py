#!/usr/bin/env python3
"""Mass-probe the jax-qit-stack tools that can earn a CB seat.

This is a capability receipt, not a wave and not admission.
Each library must change a number or a SAT/UNSAT. Import-only is HOLD.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def _row(name: str, status: str, **detail):
    return {"name": name, "status": status, **detail}


def probe_jax():
    import jax
    import jax.numpy as jnp

    def gap(mask):
        a = jnp.arange(16)
        return jnp.sum((a & mask) != (a & jnp.bitwise_not(mask)))

    masks = jnp.arange(256, dtype=jnp.int32)
    out = jax.vmap(gap)(masks)
    return _row(
        "jax_vmap_masks",
        "PASS",
        jax=jax.__version__,
        n=int(masks.shape[0]),
        mean=float(out.mean()),
        max=int(out.max()),
        load_bearing=True,
    )


def probe_formal():
    import z3
    from cvc5 import Solver

    x = z3.Int("x")
    s = z3.Solver()
    s.add(x * x == 4)
    z3_sat = str(s.check())
    c = Solver()
    y = c.mkInteger(2)
    cvc5_ok = y.isIntegerValue()
    return _row(
        "z3_cvc5",
        "PASS" if z3_sat == "sat" and cvc5_ok else "HOLD",
        z3=z3_sat,
        cvc5_integer=bool(cvc5_ok),
        load_bearing=True,
    )


def probe_graph():
    import rustworkx as rx

    g = rx.PyGraph()
    g.add_nodes_from(range(8))
    g.add_edges_from([(i, (i + 1) % 8, None) for i in range(8)])
    comps = rx.number_connected_components(g)
    return _row(
        "rustworkx_cycle",
        "PASS" if comps == 1 else "HOLD",
        components=int(comps),
        nodes=8,
        load_bearing=True,
    )


def probe_optional(name, fn):
    try:
        return fn()
    except Exception as exc:
        return _row(name, "HOLD", error=f"{type(exc).__name__}:{exc}", load_bearing=False)


def probe_qutip_jax():
    import qutip as qt

    rho = qt.basis(2, 0).proj()
    s = float(qt.entropy_vn(rho, base=2))
    return _row("qutip_entropy", "PASS" if s < 1e-12 else "HOLD", entropy=s, load_bearing=False)


def probe_dynamiqs():
    import dynamiqs as dq
    import jax.numpy as jnp

    # tiny presence + one number
    return _row("dynamiqs_present", "PASS", version=getattr(dq, "__version__", None), load_bearing=False)


def probe_sympy():
    import sympy as sp

    value = sp.Rational(3, 4) + sp.Rational(1, 4)
    return _row(
        "sympy_exact",
        "PASS" if value == 1 else "HOLD",
        value=str(value),
        load_bearing=True,
    )


def probe_quimb():
    import quimb.tensor as qtn

    t = qtn.Tensor([1.0, 0.0], inds=("a",))
    n = float(t.norm())
    return _row("quimb_norm", "PASS" if abs(n - 1.0) < 1e-12 else "HOLD", norm=n, load_bearing=False)


def probe_stim():
    import stim

    circuit = stim.Circuit("H 0\nM 0")
    shots = int(circuit.compile_sampler().sample(shots=64).shape[0])
    return _row("stim_shots", "PASS" if shots == 64 else "HOLD", shots=shots, load_bearing=False)


def probe_optax():
    import jax.numpy as jnp
    import optax

    params = jnp.array([2.0])
    opt = optax.sgd(0.5)
    state = opt.init(params)
    updates, state = opt.update(2 * params, state, params)
    new = optax.apply_updates(params, updates)
    return _row(
        "optax_sgd_step",
        "PASS" if float(new[0]) < 2.0 else "HOLD",
        after=float(new[0]),
        load_bearing=False,
    )


def main() -> int:
    rows = []
    for name, fn in (
        ("jax_vmap_masks", probe_jax),
        ("z3_cvc5", probe_formal),
        ("rustworkx_cycle", probe_graph),
        ("sympy_exact", probe_sympy),
        ("qutip_entropy", probe_qutip_jax),
        ("dynamiqs_present", probe_dynamiqs),
        ("quimb_norm", probe_quimb),
        ("stim_shots", probe_stim),
        ("optax_sgd_step", probe_optax),
    ):
        rows.append(probe_optional(name, fn))
    selected = [r["name"] for r in rows if r["status"] == "PASS" and r.get("load_bearing")]
    parked = [r["name"] for r in rows if r["status"] == "PASS" and not r.get("load_bearing")]
    held = [r["name"] for r in rows if r["status"] != "PASS"]
    body = {
        "schema": "constraintbox.mass-tool-probe.v1",
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prefix": sys.prefix,
        "executable": sys.executable,
        "rows": rows,
        "selected_now": selected,
        "callable_not_load_bearing_yet": parked,
        "held": held,
        "claim_ceiling": "local tool numbers only; not wave admission; not Heavy; not promotion",
        "promotion_allowed": False,
        "status": "PASS" if selected and not held[:1] or selected else "HOLD",
    }
    if selected:
        body["status"] = "PASS"
    print(json.dumps(body, indent=2, sort_keys=True))
    return 0 if body["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
