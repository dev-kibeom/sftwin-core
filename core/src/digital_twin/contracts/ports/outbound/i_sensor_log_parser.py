# i_sensor_log_parser.py
from typing import Protocol

from digital_twin.contracts.dtos.parsed_sensor_log_dto import ParsedSensorLogDto


class ISensorLogParser(Protocol):
    """외부 센서 로그 파일/스트림 파싱 전담 아웃바운드 포트"""

    def parse(self, file_path: str) -> ParsedSensorLogDto:
        """센서 로그 파일을 읽어 정제된 계측 데이터 맵으로 변환"""
        ...
