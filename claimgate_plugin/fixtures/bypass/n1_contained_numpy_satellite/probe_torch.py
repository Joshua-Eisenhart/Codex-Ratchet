#!/usr/bin/env python3
"""PyTorch leg — the second authoritative engine, computed independently.

Same observable as the JAX leg, different engine. Two engines agreeing is only
evidence when each leg is independently witnessed; engine_witness.py runs the
presence / poison / mutation controls over this file.
"""
import json

import torch

H = torch.tensor([[2.0, 0.5, 0.0],
                  [0.5, 3.0, 0.25],
                  [0.0, 0.25, 4.0]], dtype=torch.float64)
w = torch.linalg.eigvalsh(H)
print(json.dumps({"spectral_gap": float(w[1] - w[0]),
                  "trace": float(torch.trace(H))}))
