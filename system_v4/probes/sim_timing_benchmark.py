import os
import glob
import subprocess
import time
import json

PROBES_DIR = "system_v4/probes"
EXCLUDES = ["sim_timing_benchmark.py", "autoresearch_sim_harness.py"]
OUTPUT_JSON = "a2_state/sim_results/sim_timing_benchmark.json"

def find_sim_files():
    sim_files = []
    # Find all .py files in PROBES_DIR
    for filepath in glob.glob(os.path.join(PROBES_DIR, "*.py")):
        filename = os.path.basename(filepath)
        if filename in EXCLUDES:
            continue
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Check for if __name__ main equivalent
                if "if __name__" in content:
                    sim_files.append(filepath)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            
    return sim_files

def run_sim(filepath):
    filename = os.path.basename(filepath)
    start_time = time.time()
    
    pass_count = 0
    kill_count = 0
    stdout_lines = 0
    exit_code = -1
    
    try:
        # Run with timeout=120
        result = subprocess.run(
            ["python3", filepath], 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        exit_code = result.returncode
        stdout = result.stdout
        
        lines = stdout.splitlines()
        stdout_lines = len(lines)
        
        for line in lines:
            pass_count += line.count("PASS")
            kill_count += line.count("KILL")
                
    except subprocess.TimeoutExpired as e:
        exit_code = -9 # Use -9 or similar to denote timeout
        stdout = e.stdout
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="ignore")
        elif stdout is None:
            stdout = ""
            
        lines = stdout.splitlines()
        stdout_lines = len(lines)
        
        for line in lines:
            pass_count += line.count("PASS")
            kill_count += line.count("KILL")
            
    except Exception as e:
        print(f"Failed to run {filepath}: {e}")
    
    duration = time.time() - start_time
    
    return {
        "filename": filename,
        "duration_seconds": duration,
        "exit_code": exit_code,
        "stdout_line_count": stdout_lines,
        "pass_count": pass_count,
        "kill_count": kill_count
    }

def main():
    sim_files = find_sim_files()
    results = []
    
    print(f"Found {len(sim_files)} SIM files to benchmark.")
    
    for filepath in sim_files:
        print(f"Running {filepath}...")
        res = run_sim(filepath)
        results.append(res)
        
    # Sort by duration slowest first
    results.sort(key=lambda x: x["duration_seconds"], reverse=True)
    
    # Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nSaved JSON results to {OUTPUT_JSON}")
        
    # Print formatted table
    print("\nBenchmark Results:")
    print(f"{'file':<40} | {'time(s)':<8} | {'exit':<4} | {'PASS':<4} | {'KILL':<4}")
    print("-" * 75)
    
    for r in results:
        print(f"{r['filename']:<40} | {r['duration_seconds']:<8.2f} | {r['exit_code']:<4} | {r['pass_count']:<4} | {r['kill_count']:<4}")

    # Identify 5 slowest
    print("\nTop 5 Slowest SIMs:")
    for r in results[:5]:
        print(f"{r['filename']} ({r['duration_seconds']:.2f}s)")

if __name__ == "__main__":
    main()
