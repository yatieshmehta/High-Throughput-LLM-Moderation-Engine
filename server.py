import time
import uuid
import json
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm import SamplingParams
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge

app = FastAPI(title="High-Throughput Moderation API")

# --- Production Observability (JD Requirement) ---
GPU_MEM_GAUGE = Gauge("gpu_vram_usage_bytes", "Current GPU VRAM usage in bytes")

# --- Inference Engine Setup ---
engine_args = AsyncEngineArgs(
    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    gpu_memory_utilization=0.8,
    enable_chunked_prefill=True  # Optimization for TTFT
)
engine = AsyncLLMEngine.from_engine_args(engine_args)

class ModerationRequest(BaseModel):
    prompt: str = Field(..., max_length=1000)
    max_tokens: int = 64

@app.get("/health")
async def health():
    """Health check for load balancers (Circuit Breaker)"""
    vram_used = torch.cuda.memory_allocated()
    GPU_MEM_GAUGE.set(vram_used)
    # If VRAM > 90%, we signal we are 'Unhealthy' to avoid a crash
    if vram_used > 0.90 * 8188 * 1024 * 1024:
        raise HTTPException(status_code=503, detail="GPU Saturated")
    return {"status": "ready", "vram_utilization": vram_used}

# ... (Keep existing imports from previous server.py)

# Specific Moderation Prompt to ensure structured output
MODERATION_SYSTEM_PROMPT = """
You are a content moderation AI. Analyze the user text for toxicity, hate speech, or violence.
Return ONLY a JSON object in this format:
{"is_toxic": boolean, "confidence": float, "category": string}
"""

@app.post("/v1/moderate")
async def moderate(req: ModerationRequest):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    
    # We combine system instructions with user input
    full_prompt = f"{MODERATION_SYSTEM_PROMPT}\nUser Text: {req.prompt}\nResult:"
    
    sampling_params = SamplingParams(
        temperature=0.0, # Zero temperature for deterministic classification
        max_tokens=req.max_tokens,
        stop=["\n"] # Stop at the end of the JSON line
    )
    
    async def stream_results():
        ttft = None
        async for output in engine.generate(full_prompt, sampling_params, request_id):
            if ttft is None:
                ttft = time.perf_counter() - start_time
            
            # Extract the generated text
            generated_text = output.outputs[0].text
            yield json.dumps({
                "structured_output": generated_text,
                "ttft_sec": ttft,
                "request_id": request_id
            }) + "\n"

    return StreamingResponse(stream_results(), media_type="application/x-ndjson")

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app)