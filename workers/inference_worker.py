import os
import sys
import redis
from rq import Worker, Queue

LISTEN_QUEUES = ["inference_queue"]

def run_inference_worker():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"[Inference Worker] Connecting to Redis: {redis_url}")
    conn = redis.from_url(redis_url)

    queues = [Queue(name, connection=conn) for name in LISTEN_QUEUES]
    worker = Worker(queues, connection=conn)
    print(f"[Inference Worker] Inference Worker ready! Listening on queues: {LISTEN_QUEUES}")
    worker.work(with_scheduler=True)

if __name__ == "__main__":
    run_inference_worker()
