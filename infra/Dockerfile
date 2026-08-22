FROM python:3.11-slim AS base
WORKDIR /app

# 1. 파일 복사
COPY dependencies.py ./
COPY core/pyproject.toml ./core/
COPY core/ ./core/
COPY plugins/ ./plugins/

# 2. uvicorn 및 프로젝트 의존성 설치
RUN pip install --no-cache-dir "uvicorn[standard]" fastapi && \
    pip install --no-cache-dir -e ./core

# 3. editable 패키지 설치 (core 디렉터리 기준 설치)
RUN pip install --no-cache-dir -e ./core

# --- 각 서비스 타깃 ---
FROM base AS asset-svc
CMD ["uvicorn", "plugins.fast_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS sim-svc
CMD ["uvicorn", "plugins.fast_api.main:app", "--host", "0.0.0.0", "--port", "8001"]

FROM base AS kpi-svc
CMD ["uvicorn", "plugins.fast_api.main:app", "--host", "0.0.0.0", "--port", "8002"]
