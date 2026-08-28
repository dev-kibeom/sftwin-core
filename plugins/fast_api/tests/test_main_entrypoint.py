# File: plugins/fast_api/tests/test_main_entrypoint.py

import os
from unittest.mock import patch
import pytest
from fastapi import FastAPI

import plugins.fast_api.main as main_module


def test_main_module_exports_fastapi_app_instance():
    # Given & When: main 모듈 로드

    # Then: app 객체가 FastAPI 인스턴스여야 함
    assert hasattr(main_module, "app")
    assert isinstance(main_module.app, FastAPI)


@patch("uvicorn.run")
def test_run_server_with_default_configurations(mock_uvicorn_run):
    # Given: 환경 변수가 비어있는 상태
    with patch.dict(os.environ, {}, clear=True):
        # When
        main_module.run()

        # Then: 기본 설정(0.0.0.0, 8000, info, False)으로 uvicorn.run 호출 검증
        mock_uvicorn_run.assert_called_once_with(
            "plugins.fast_api.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,
        )


@patch("uvicorn.run")
def test_run_server_with_custom_environment_variables(mock_uvicorn_run):
    # Given: 사용자 지정 환경 변수 설정
    custom_env = {
        "FASTAPI_HOST": "127.0.0.1",
        "FASTAPI_PORT": "9000",
        "FASTAPI_LOG_LEVEL": "debug",
        "FASTAPI_RELOAD": "true",
    }
    with patch.dict(os.environ, custom_env, clear=True):
        # When
        main_module.run()

        # Then: 환경 변수가 파싱되어 uvicorn.run에 전달되는지 검증
        mock_uvicorn_run.assert_called_once_with(
            "plugins.fast_api.main:app",
            host="127.0.0.1",
            port=9000,
            log_level="debug",
            reload=True,
        )
