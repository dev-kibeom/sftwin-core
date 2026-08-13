"""
===============================================================================
[File Name] i_sensor_log_parser.py
[Location ] core/src/asset_twin/twin_reconstruction/ports/outbound/i_sensor_log_parser.py
[Description]
 - 센서 로그 파싱 및 트윈 베이스라인 구축 전담 포트 인터페이스입니다.
 - 특정 파싱 기술(pandas/Adapter) 명칭을 포트 계층에서 완벽히 격리합니다.
===============================================================================
"""

from abc import ABC, abstractmethod

from asset_twin.twin_reconstruction.domain.twin_baseline import TwinBaseline


class ISensorLogParser(ABC):
    @abstractmethod
    def parse_sensor_log(self, file_path: str) -> TwinBaseline:
        """
        입력된 센서 로그 파일 경로를 파싱하여 TwinBaseline 도메인 객체 반환
        """
        pass
