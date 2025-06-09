FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libatlas-base-dev \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY intent_model.joblib ./intent_model.joblib

COPY . .

RUN mkdir -p /app/results /app/models

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    OLLAMA_HOST=host.docker.internal

CMD ["python", "main.py"]