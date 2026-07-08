Install: python3 -m pip install numpy scipy
Run: python3 run_replication.py --seed 11
Use a seed you choose before looking at expected_ours.json.

The script fits a full affine Bloch channel map r' = A r + b for each of the
16 UP-100 stages from a training probe set, then re-identifies each stage from a
disjoint novel probe set by nearest full affine map.

PASS means:
1. full affine map re-identification is 16/16;
2. minimum separation margin is greater than 10x maximum same-stage self-noise;
3. the SVD(A)-only contrast re-identifies fewer than 16/16 and collapses at
   least one chirality-mirror pair among t1/t5 or t3/t7.

FAIL means the frozen criteria did not reproduce for that seed.
Results JSON is written as results_seed_<seed>.json unless --output is supplied.
Compare to expected_ours.json only after recording your run.
Send results JSON and stdout to the packet sender.
