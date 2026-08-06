# HONEST torch leg: every printed number is computed by torch at run time.
import json
import torch

p = torch.tensor([0.25, 0.25, 0.25, 0.25], dtype=torch.float64)
rank = int((p > 0.001).sum().item())
S0 = float(torch.log2(torch.tensor(float(rank), dtype=torch.float64)))
S2 = float(-torch.log2(torch.dot(p, p)))
print(json.dumps({"S_0_bits": S0, "S_2_bits": S2, "trace": float(p.sum())}))
