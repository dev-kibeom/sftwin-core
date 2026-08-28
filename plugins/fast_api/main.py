# File: plugins/fast_api/main.py
import os

import uvicorn
from fastapi import FastAPI

from plugins.fast_api.app import create_app

# 외장 ASGI 실행기(Uvicorn/Gunicorn CLI)에서 참조할 모듈 레벨 앱 인스턴스
app: FastAPI = create_app()


def run() -> None:
    """환경 변수 기반으로 Uvicorn 서버를 실행하는 엔트리포인트 함수"""
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "8000"))
    log_level = os.getenv("FASTAPI_LOG_LEVEL", "info")
    reload_flag = os.getenv("FASTAPI_RELOAD", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    uvicorn.run(
        "plugins.fast_api.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload_flag,
    )


if __name__ == "__main__":
    run()
