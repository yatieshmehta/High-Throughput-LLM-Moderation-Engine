import matplotlib.pyplot as plt
import pandas as pd
import os

# Define the source folder
RESULTS_DIR = "benchmarks_results"
summary_file = os.path.join(RESULTS_DIR, "production_scaling_report.csv")

if not os.path.exists(summary_file):
    print(f"Error: {summary_file} not found. Run benchmarks.py first.")
else:
    df = pd.read_csv(summary_file)

    plt.figure(figsize=(12, 5))

    # Plot 1: Latency Metrics (Observability)
    # We plot both P95 Total and P95 TTFT to show the overhead of generation
    plt.subplot(1, 2, 1)
    plt.plot(df['users'], df['p95_ttft_ms'], marker='o', label='TTFT (P95)', color='#1f77b4')
    plt.plot(df['users'], df['p95_total_latency_ms'], marker='s', label='Total Latency (P95)', color='#ff7f0e')
    plt.xlabel("Concurrent Users")
    plt.ylabel("Latency (ms)")
    plt.title("Latency vs. Concurrency Sweep")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)

    # Plot 2: Throughput (Scaling Strategy)
    # This shows where the RTX 4060 hits its limit
    plt.subplot(1, 2, 2)
    plt.plot(df['users'], df['rps'], marker='^', color='#2ca02c', linewidth=2)
    plt.xlabel("Concurrent Users")
    plt.ylabel("Requests Per Second (RPS)")
    plt.title("Throughput Saturation Frontier")
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    
    # Save the output back into the results folder
    plot_path = os.path.join(RESULTS_DIR, "inference_performance_viz.png")
    plt.savefig(plot_path)
    print(f"Visualization saved to: {plot_path}")
    plt.show()