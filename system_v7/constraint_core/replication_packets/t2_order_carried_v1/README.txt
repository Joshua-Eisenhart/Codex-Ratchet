Install: python3 -m pip install numpy scipy pysindy
Run: python3 run_replication.py --seed 7
Use a seed you choose before looking at expected_ours.json.
The script prints ordered distance, unordered distance, null band, and PASS/FAIL.
PASS means ordered distance is above null band and unordered distance is within it.
FAIL means the frozen criteria did not reproduce for that seed or the instrument gate failed.
Results JSON is written as results_seed_<seed>.json unless --output is supplied.
Compare to expected_ours.json only after recording your run.
Send results JSON and stdout to the packet sender.
