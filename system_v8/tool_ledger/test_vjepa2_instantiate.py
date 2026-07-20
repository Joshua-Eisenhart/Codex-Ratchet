"""
vjepa2 (facebookresearch official) integration test — IMPORT + config-load + tiny
instantiate only (no video training). Owner scope: this is a large vision model;
we check whether the officially-shipped encoder/predictor classes exist and can
be instantiated at tiny size in this env, nothing more.

facebookresearch/vjepa2 does not ship a standalone pip package. The officially
supported integration path for the released checkpoints is via HuggingFace
`transformers` (transformers.models.vjepa2 — VJEPA2Model / VJEPA2Config /
VJEPA2Encoder / VJEPA2Predictor), which is what this test exercises.
"""
import json
import sys
import traceback
from pathlib import Path

OUT = Path(__file__).parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

result = {"donor": "vjepa2", "checks": {}}

# 1. availability check
try:
    import transformers
    result["checks"]["transformers_version"] = transformers.__version__
    from transformers.models import vjepa2 as vjepa2_pkg
    result["checks"]["vjepa2_module_path"] = vjepa2_pkg.__file__
    result["checks"]["pip_package_vjepa2_exists"] = False
    result["checks"]["available_via"] = "transformers.models.vjepa2 (bundled, official HF integration for facebookresearch/vjepa2 checkpoints)"
except Exception as exc:
    result["checks"]["import_error"] = repr(exc)
    result["verdict"] = "BLOCKED"
    result["reason"] = f"transformers.models.vjepa2 not importable: {exc!r}"
    with open(OUT / "vjepa2_result.json", "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps(result, indent=2))
    sys.exit(0)

# 2. config-load: build a TINY config (far below the released 1024-hidden/24-layer
#    encoder) purely to test the class wiring, not to represent a usable model.
# NOTE: an initial pass at hidden_size=32/pred_hidden_size=16 (attention_head_size
# 16 and 8) hit a real shape bug in the shipped rotary-embedding code
# (transformers/models/vjepa2/modeling_vjepa2.py: rotate_queries_or_keys), which
# only manifests when the rotary sub-dim D satisfies D//2==1 (an absurdly tiny
# corner case that never occurs at released checkpoint scale). That failure is
# recorded below as `first_attempt_tiny_config_error`. hidden_size=48 avoids the
# corner case (D//2==4) and is still ~20x smaller than the released encoder.
try:
    from transformers import VJEPA2Config, VJEPA2Model

    first_attempt_config = VJEPA2Config(
        patch_size=16, crop_size=32, frames_per_clip=4, tubelet_size=2,
        hidden_size=32, in_chans=3, num_attention_heads=2, num_hidden_layers=1,
        pred_hidden_size=16, pred_num_attention_heads=2, pred_num_hidden_layers=1,
        pred_num_mask_tokens=2,
    )
    try:
        import torch as _torch
        _m = VJEPA2Model(first_attempt_config)
        _pv = _torch.randn(1, first_attempt_config.frames_per_clip, 3,
                            first_attempt_config.crop_size, first_attempt_config.crop_size)
        _m(pixel_values_videos=_pv)
        result["checks"]["first_attempt_tiny_config_error"] = None
    except Exception as first_exc:
        result["checks"]["first_attempt_tiny_config_error"] = repr(first_exc)

    tiny_config = VJEPA2Config(
        patch_size=16,
        crop_size=32,          # tiny spatial size (released default: 256)
        frames_per_clip=4,     # tiny temporal size (released default: 64)
        tubelet_size=2,
        hidden_size=48,        # tiny (released default: 1024)
        in_chans=3,
        num_attention_heads=2,
        num_hidden_layers=2,   # tiny (released default: 24)
        pred_hidden_size=48,   # tiny (released default: 384)
        pred_num_attention_heads=2,
        pred_num_hidden_layers=2,  # tiny (released default: 12)
        pred_num_mask_tokens=2,
    )
    result["checks"]["config_load"] = "ok"
    result["checks"]["tiny_config"] = tiny_config.to_dict()
except Exception as exc:
    result["checks"]["config_error"] = repr(exc)
    result["checks"]["config_traceback"] = traceback.format_exc()
    result["verdict"] = "BLOCKED"
    result["reason"] = f"VJEPA2Config construction failed: {exc!r}"
    with open(OUT / "vjepa2_result.json", "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps(result, indent=2))
    sys.exit(0)

# 3. tiny instantiate: build the model (random init, no pretrained weights) and
#    run a single tiny forward pass to confirm the encoder/predictor wiring runs.
try:
    import torch
    torch.manual_seed(0)
    model = VJEPA2Model(tiny_config)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    result["checks"]["model_instantiate"] = "ok"
    result["checks"]["n_params"] = n_params

    # tiny pixel_values_videos: (batch, frames, channels, height, width)
    pixel_values_videos = torch.randn(
        1, tiny_config.frames_per_clip, 3, tiny_config.crop_size, tiny_config.crop_size
    )
    with torch.no_grad():
        out = model(pixel_values_videos=pixel_values_videos)
    last_hidden_shape = list(out.last_hidden_state.shape)
    result["checks"]["forward_pass"] = "ok"
    result["checks"]["last_hidden_state_shape"] = last_hidden_shape

    result["verdict"] = "INTEGRATED"
    result["reason"] = (
        f"transformers.models.vjepa2 VJEPA2Model instantiated tiny ({n_params} params, "
        f"hidden_size=48/pred_hidden_size=48) and ran one forward pass on a random tiny "
        f"video tensor -> last_hidden_state shape {last_hidden_shape}. No pretrained "
        f"weights loaded, no real video training — import+config-load+tiny-instantiate "
        f"only, per scope. An even-tinier first-attempt config (hidden_size=32/"
        f"pred_hidden_size=16) hit a real library rotary-embedding shape bug "
        f"(see first_attempt_tiny_config_error) that does not occur at this or at "
        f"released-checkpoint scale."
    )
except Exception as exc:
    result["checks"]["instantiate_error"] = repr(exc)
    result["checks"]["instantiate_traceback"] = traceback.format_exc()
    result["verdict"] = "BLOCKED"
    result["reason"] = f"VJEPA2Model tiny instantiate/forward failed: {exc!r}"

with open(OUT / "vjepa2_result.json", "w") as fh:
    json.dump(result, fh, indent=2)
print(json.dumps(result, indent=2))
