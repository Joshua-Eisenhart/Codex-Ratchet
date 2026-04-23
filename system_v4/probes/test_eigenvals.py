import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from abiogenesis_v2_sim import sim_abiogenesis_topologies
sim_abiogenesis_topologies()
