import subprocess
import pandas as pd
import os

# Define the results directory
RESULTS_DIR = "benchmarks_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

concurrencies = [1, 10, 30, 50, 75, 100]
final_results = []

for c in concurrencies:
    print(f"--- Stress Testing Concurrency: {c} ---")
    
    # Prefix the CSV path with the results directory
    csv_prefix = os.path.join(RESULTS_DIR, f"run_c{c}")
    
    # Run locust
    cmd = f"locust -f locustfile.py --headless -u {c} -r {c} --run-time 60s --csv={csv_prefix} --host=http://localhost:8000"
    subprocess.run(cmd, shell=True)
    
    # Access the file from the subdirectory
    stats_file = f"{csv_prefix}_stats.csv"
    if os.path.exists(stats_file):
        df = pd.read_csv(stats_file)
        agg = df[df['Name'] == 'Aggregated']
        ttft_row = df[df['Name'] == 'TTFT']
        p95_ttft = ttft_row['95%'].values[0] if not ttft_row.empty else 0
        
        final_results.append({
            "users": c,
            "rps": agg['Request Count'].values[0] / 60,
            "p95_total_latency_ms": agg['95%'].values[0],
            "p95_ttft_ms": p95_ttft,
            "failures": agg['Failure Count'].values[0]
        })

# Save the final summary inside the same folder
summary_path = os.path.join(RESULTS_DIR, "production_scaling_report.csv")
pd.DataFrame(final_results).to_csv(summary_path, index=False)
print(f"All logs and summary saved in: {RESULTS_DIR}/")