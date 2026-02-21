# High-Throughput Content Moderation Inference Service
**Production-grade LLM Serving with vLLM, FastAPI, and Prometheus**

An asynchronous, high-availability inference gateway designed for real-time text classification. This service leverages **PagedAttention** and **Continuous Batching** to provide a scalable "Moderation-as-a-Service" platform capable of handling extreme concurrency on consumer-grade hardware.

The system is engineered to solve the primary challenges of distributed inference: minimal latency, efficient load balancing, and high observability.

## 📊 Performance Analysis (NVIDIA RTX 4060)
The following data was captured via a custom-built concurrency sweep (1–100 users) to identify the hardware's **Saturation Frontier**.

| Concurrent Users | Throughput (RPS) | P95 TTFT (ms) | P95 Total Latency (ms) | Failures |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 5.15 | 21 | 270 | 0 |
| 10 | 51.42 | 32 | 290 | 0 |
| 30 | 142.50 | 39 | 340 | 0 |
| 50 | 214.68 | 50 | 410 | 0 |
| 75 | 269.57 | 69 | 560 | 0 |
| **100** | **294.92** | **95** | **760** | **0** |

### 🔍 System Bottleneck Analysis
* **Throughput Saturation:** The system achieved a peak of **294.92 RPS**. As concurrency increased from 75 to 100, the RPS gains began to plateau, indicating the transition from a compute-bound (prefill) to a memory-bandwidth bound (decode) state on the 8GB RTX 4060.
* **TTFT Stability:** Time to First Token (TTFT) remained under 100ms even at 100x baseline load. This validates the effectiveness of **Continuous Batching** and **Chunked Prefill** in preventing head-of-line blocking for new requests.
* **P95 Tail Behavior:** Total latency grew from 270ms to 760ms. This divergence from TTFT highlights the auto-regressive decoding phase as the primary system bottleneck under heavy load.

## 🛠️ Infrastructure & Resilience
* **Observability:** Integrated **Prometheus** instrumentation to expose real-time request histograms and hardware-level VRAM saturation metrics.
* **Circuit Breaker:** Implemented an automated health-check mechanism that monitors GPU memory. To ensure high reliability, the system signals **503 Service Unavailable** once VRAM utilization exceeds 90%, preventing OOM (Out of Memory) crashes.
* **Structured Output:** Utilizes system prompting and zero-temperature sampling to enforce deterministic JSON outputs, ensuring the service is ready for downstream automated workflows.

## 📦 Deployment & Setup



### Dockerized Execution (Recommended)
This ensures a reproducible environment for distributed infrastructure.

`docker build -t moderation-service .`
`docker run --gpus all -p 8000:8000 moderation-service`

### Manual Installation
1. Install dependencies: `pip install vllm fastapi uvicorn prometheus-fastapi-instrumentator`
2. Start the server: `uvicorn server:app --host 0.0.0.0 --port 8000`
3. Run benchmarks: `python benchmarks.py`

## 📈 Scaling Roadmap
Based on empirical data, a single RTX 4060 node sustains ~300 RPS before violating a 1s latency budget. To support a production requirement of **1,000+ RPS**, the suggested strategy is a horizontal cluster of **4-5 GPU nodes** managed by a round-robin load balancer.
