import os
import sys
import redis
from rq import Worker, Queue, Connection

LISTEN_QUEUES = ["training_queue", "default"]

def run_worker():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"[Trainer Worker] Connecting to Redis: {redis_url}")
    conn = redis.from_url(redis_url)

    with Connection(conn):
        worker = Worker(map(Queue, LISTEN_QUEUES))
        print(f"[Trainer Worker] Worker ready, listening on queues: {LISTEN_QUEUES}")
        worker.work(with_scheduler=True)

if __name__ == "__main__":
    run_worker()
