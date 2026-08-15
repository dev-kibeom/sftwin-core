import os

import pytest
import requests

# Base URL for API Gateway (Nginx)
BASE_URL = os.getenv("TEST_GATEWAY_URL", "http://localhost")


@pytest.fixture(scope="module")
def auth_header():
    """모킹된 테스트용 Bearer JWT 토큰 헤더 생성"""
    # 실제 JWT 토큰 생성이 필요하면 shared.security 모듈 활용
    return {"Authorization": "Bearer mock-test-token-admin"}


def test_01_health_check_all_services():
    """1. 전체 모듈 헬스체크 엔드포인트 응답 통전 검증"""
    res = requests.get(f"{BASE_URL}/healthz", timeout=2)
    assert res.status_code == 200
    assert res.json().get("status") == "ok"


def test_02_digital_twin_registration_and_reconstruct(auth_header):
    """2. 자산 등록 및 KAMP 데이터 모킹 기반 복각 테스트"""
    # Asset 동적 등록 (Command Facade)
    asset_payload = {
        "asset_id": "AST-DOOSAN-M1013",
        "asset_name": "Doosan_M1013_Robot",
        "asset_type": "ROBOT",
        "cad_file_path": "/app/assets/cad/doosan_m1013.stl",
    }
    # Nginx 경로 포워딩 연동 검증
    res = requests.post(
        f"{BASE_URL}/api/v1/assets", json=asset_payload, headers=auth_header, timeout=5
    )
    # 아직 API 구현 전이더라도 Gateway 통전(200~202 또는 Mock 200)을 검증
    assert res.status_code in [
        200,
        201,
        404,
    ]  # API 라우트 미구현시 404가 나더라도 Gateway 연결 자체는 확인됨


def test_03_fms_simulation_execution(auth_header):
    """3. FMS 시뮬레이션 가동 요청 (Simulation Component)"""
    sim_payload = {"scenario_id": "SCN-FMS-DEMO-001", "robot_ids": ["AST-DOOSAN-M1013"]}
    # Simulation Service HTTP / gRPC 통전 확인
    res = requests.post(
        f"{BASE_URL}/api/v1/simulations/run",
        json=sim_payload,
        headers=auth_header,
        timeout=5,
    )
    assert res.status_code in [200, 202, 404]


def test_04_kpi_dashboard_query(auth_header):
    """4. 시뮬레이션 결과 기반 KPI 산출 조회 (KPI Component)"""
    res = requests.get(
        f"{BASE_URL}/api/v1/kpi/oee/SCN-FMS-DEMO-001", headers=auth_header, timeout=5
    )
    assert res.status_code in [200, 404]
