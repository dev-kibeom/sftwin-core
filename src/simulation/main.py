from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(title="Simulation & Physics Service", version="1.0.0")


@app.get("/healthz")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/simulations/healthz")
async def api_health_check():
    return {
        "status": "ok",
        "service": "simulation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
