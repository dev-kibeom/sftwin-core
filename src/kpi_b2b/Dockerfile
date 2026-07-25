FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn pydantic

COPY src/kpi_b2b /app/src/kpi_b2b
COPY src/shared /app/src/shared

ENV PYTHONPATH=/app

CMD ["uvicorn", "src.kpi_b2b.main:app", "--host", "0.0.0.0", "--port", "8002"]