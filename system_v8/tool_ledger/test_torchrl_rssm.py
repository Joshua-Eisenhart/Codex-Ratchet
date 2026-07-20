"""
TorchRL integration test (donor #1: RSSM/world-model components).

Scope per task: import test; if present/installable, build a MINIMAL RSSM-style
latent rollout on the REAL world-source view sequences (few steps, tiny model)
and verify loss decreases. INTEGRATED if it runs, BLOCKED with exact error
otherwise.

Data: system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl
64 objects x 6 views x 8 probes (occluded views have withheld probe outcomes).
Each object's 6-view sequence is treated as a rollout: observation_t (8-dim
probe-outcome vector, occluded entries marked -1) -> deterministic recurrent
latent state (torchrl.modules.GRUModule) -> observation reconstruction head,
wired through TensorDictModule/TensorDictSequential and torchrl.modules
WorldModelWrapper (transition_model + reward_model), i.e. genuine torchrl
world-model machinery, not a bare torch.nn.GRU.
"""
import json
import sys
import traceback
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVENTS = REPO / "system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl"
OUT = Path(__file__).parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

result = {"donor": "torchrl", "checks": {}}


def load_sequences():
    objs = defaultdict(lambda: defaultdict(dict))
    with open(EVENTS) as fh:
        for line in fh:
            d = json.loads(line)
            p = d["payload"]["operations"][0]["payload"]
            claims = {c["predicate"]: c["object"] for c in p["claims"]}
            oid = claims["has_object_id"]
            view = int(claims["view_index"])
            pos = int(claims["probe_position"])
            outcome = claims["probe_outcome"]
            val = -1.0 if outcome == "withheld" else float(outcome)
            objs[oid][view][pos] = val
    object_ids = sorted(objs)
    n_views = len(objs[object_ids[0]])
    n_probes = len(objs[object_ids[0]][0])
    return objs, object_ids, n_views, n_probes


try:
    import torch
    import torch.nn as nn
    result["checks"]["torch_version"] = torch.__version__

    import torchrl
    result["checks"]["torchrl_version"] = torchrl.__version__
    from torchrl.modules import GRUModule, WorldModelWrapper
    from tensordict import TensorDict
    from tensordict.nn import TensorDictModule, TensorDictSequential
    import tensordict
    result["checks"]["tensordict_version"] = tensordict.__version__
    result["checks"]["import"] = "ok"
except Exception as exc:
    result["checks"]["import_error"] = repr(exc)
    result["verdict"] = "BLOCKED"
    result["reason"] = f"torchrl (or its tensordict dependency) not importable: {exc!r}"
    with open(OUT / "torchrl_result.json", "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps(result, indent=2))
    sys.exit(0)

try:
    objs, object_ids, n_views, n_probes = load_sequences()
    result["checks"]["n_objects"] = len(object_ids)
    result["checks"]["n_views"] = n_views
    result["checks"]["n_probes"] = n_probes

    # (n_objects, n_views, n_probes)
    data = torch.zeros(len(object_ids), n_views, n_probes)
    for oi, oid in enumerate(object_ids):
        for vi in range(n_views):
            for pi in range(n_probes):
                data[oi, vi, pi] = objs[oid][vi][pi]

    torch.manual_seed(0)
    hidden_size = 12
    obs_dim = n_probes

    # default_recurrent_mode=True: process the full (n_objects, n_views) time
    # axis in one call, per torchrl >=0.8 API (set_recurrent_mode() context
    # manager / constructor kwarg replaced the removed .set_recurrent_mode()
    # instance method).
    gru = GRUModule(
        input_size=obs_dim,
        hidden_size=hidden_size,
        in_keys=["obs", "recurrent_state", "is_init"],
        out_keys=["latent", ("next", "recurrent_state")],
        default_recurrent_mode=True,
    )

    decoder = TensorDictModule(
        nn.Linear(hidden_size, obs_dim),
        in_keys=["latent"],
        out_keys=["obs_pred"],
    )

    reward_head = TensorDictModule(
        nn.Linear(hidden_size, 1),
        in_keys=["latent"],
        out_keys=["reward_pred"],
    )

    # torchrl's WorldModelWrapper: transition_model (recurrent latent update +
    # observation-reconstruction decoder) + reward_model, genuine world-model
    # composition (not a bare nn.GRU).
    transition_model = TensorDictSequential(gru, decoder)
    world_model = WorldModelWrapper(transition_model=transition_model, reward_model=reward_head)
    result["checks"]["world_model_build"] = "ok"

    params = list(world_model.parameters())
    result["checks"]["n_params"] = sum(p.numel() for p in params)
    opt = torch.optim.Adam(params, lr=5e-2)

    losses = []
    n_epochs = 60
    for epoch in range(n_epochs):
        td = TensorDict(
            {
                "obs": data,
                "is_init": torch.zeros(len(object_ids), n_views, 1, dtype=torch.bool),
            },
            batch_size=[len(object_ids), n_views],
        )
        td["is_init"][:, 0] = True
        out = world_model(td)
        # predict obs_pred[t] ~ obs[t] (autoencoding through the recurrent latent,
        # i.e. can the recurrent latent state reconstruct the occluded-probe view
        # sequence it was built from) -- this is the loss torchrl RSSM-style
        # world-models are trained against (reconstruction term of the ELBO).
        loss = ((out["obs_pred"] - data) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))

    result["checks"]["losses_first5"] = losses[:5]
    result["checks"]["losses_last5"] = losses[-5:]
    result["checks"]["loss_start"] = losses[0]
    result["checks"]["loss_end"] = losses[-1]
    loss_decreased = losses[-1] < losses[0]
    result["checks"]["loss_decreased"] = loss_decreased

    if loss_decreased:
        result["verdict"] = "INTEGRATED"
        result["reason"] = (
            f"torchrl.modules.GRUModule + WorldModelWrapper (transition_model="
            f"GRUModule->decoder, reward_model=linear head) trained {n_epochs} steps "
            f"on the real 64-object x {n_views}-view x {n_probes}-probe occluded-view "
            f"sequences from events_dynamics_on.jsonl. Reconstruction MSE loss "
            f"{losses[0]:.4f} -> {losses[-1]:.4f} (decreased). {sum(p.numel() for p in params)} params."
        )
    else:
        result["verdict"] = "BLOCKED"
        result["reason"] = (
            f"Ran without error but loss did not decrease: {losses[0]:.4f} -> {losses[-1]:.4f}"
        )
except Exception as exc:
    result["checks"]["run_error"] = repr(exc)
    result["checks"]["run_traceback"] = traceback.format_exc()
    result["verdict"] = "BLOCKED"
    result["reason"] = f"RSSM-style rollout build/train failed: {exc!r}"

with open(OUT / "torchrl_result.json", "w") as fh:
    json.dump(result, fh, indent=2)
print(json.dumps(result, indent=2))
