from datetime import datetime, timezone

from fastapi import FastAPI

from src.kpi_b2b.routers import kpi_router, procurement_router

app = FastAPI(title="KPI & B2B Service", version="1.0.0")

# 신규 라우터 등록
app.include_router(kpi_router.router)
app.include_router(procurement_router.router)


@app.get("/healthz")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
