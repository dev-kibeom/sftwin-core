import json
import logging
from unittest.mock import patch

from shared.context.log_context import LogContext
from shared.logger.global_system_logger import GlobalSystemLogger


def test_tc_log_system_logger_json_formatting():
    system_logger = GlobalSystemLogger(
        component_name="TestComponent", logger_name="sftwin.global"
    )
    log_ctx = LogContext(trace_id="TRC-1234", context={"service": "auth"})

    # 내부 logging.Logger.log 호출 및 JSON 페이로드 검증
    with (
        patch.object(system_logger._logger, "isEnabledFor", return_value=True),
        patch.object(system_logger._logger, "log") as mock_log,
    ):
        system_logger.info(message="System initialisation complete", log_ctx=log_ctx)

        mock_log.assert_called_once()
        called_level, called_json_str = mock_log.call_args[0]

        # 로그 레벨 확인
        assert called_level == logging.INFO

        # 직렬화된 JSON 구조 및 필드 검증
        log_payload = json.loads(called_json_str)
        assert log_payload["component"] == "TestComponent"
        assert log_payload["log_level"] == "INFO"
        assert log_payload["trace_id"] == "TRC-1234"
        assert log_payload["context"]["service"] == "auth"
