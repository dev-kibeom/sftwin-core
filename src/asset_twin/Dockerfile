FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn pydantic pyjwt cryptography sqlalchemy pandas

COPY src/asset_twin /app/src/asset_twin
COPY src/shared /app/src/shared

ENV PYTHONPATH=/app

CMD ["uvicorn", "src.asset_twin.main:app", "--host", "0.0.0.0", "--port", "8000"]