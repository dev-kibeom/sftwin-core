from dataclasses import dataclass


@dataclass(frozen=True)
class RawFactoryDataDto:
    """원천 공장 센서 로그 데이터 요청 Input DTO"""

    baseline_name: str
    source_log_path: str
