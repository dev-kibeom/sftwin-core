from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(title="KPI & B2B Service", version="1.0.0")


@app.get("/healthz")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/kpi/healthz")
async def api_health_check():
    return {
        "status": "ok",
        "service": "kpi_b2b",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
