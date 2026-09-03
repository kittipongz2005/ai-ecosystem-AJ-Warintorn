FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY workers/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY workers /app/workers
COPY backend /app/backend
COPY utils /app/utils

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

CMD ["python", "workers/worker.py"]
