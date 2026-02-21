from locust import HttpUser, task, between, events
import time
import random

# Real-world moderation samples
SAMPLES = [
    "I love this product, it's amazing!",
    "You are a total idiot and I hate you.",
    "The weather is quite nice in Waterloo today.",
    "I am going to punch someone in the face.",
    "This is a very helpful tutorial, thank you."
]

class ModerationUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def check_moderation(self):
        sample = random.choice(SAMPLES)
        start_perf = time.perf_counter()
        ttft = None
        
        with self.client.post("/v1/moderate", json={
            "prompt": sample,
            "max_tokens": 50
        }, stream=True, catch_response=True) as response:
            try:
                for line in response.iter_lines():
                    if ttft is None:
                        ttft = (time.perf_counter() - start_perf) * 1000
                        # Log custom TTFT metric for Cerebras Observability requirement
                        events.request.fire(
                            request_type="LLM",
                            name="TTFT",
                            response_time=ttft,
                            response_length=0
                        )
                
                total_latency = (time.perf_counter() - start_perf) * 1000
                events.request.fire(
                    request_type="LLM",
                    name="Total_Latency",
                    response_time=total_latency,
                    response_length=0
                )
                response.success()
            except Exception as e:
                response.failure(str(e))