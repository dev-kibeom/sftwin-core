"""
@file hotspot_color_calculator.py
@description Real-to-Sim 정합성 오차율(%)을 기반으로 3D 캔버스 설비 핫스팟 색상을 도출하는 도메인 서비스
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HotspotColorResult:
    status_code: str  # NORMAL, WARNING, EXCEEDED
    color_hex: str  # #0000FF(Blue), #FFFF00(Yellow), #FF0000(Red)


class HotspotColorCalculator:
    """프레임워크 독립적인 Pure Domain Service"""

    def calculate_color(self, error_rate_percent: float) -> HotspotColorResult:
        if error_rate_percent <= 3.0:
            return HotspotColorResult(
                status_code="NORMAL", color_hex="#0000FF"
            )  # 푸른색 (정상)
        elif error_rate_percent <= 5.0:
            return HotspotColorResult(
                status_code="WARNING", color_hex="#FFFF00"
            )  # 노란색 (주의)
        else:
            return HotspotColorResult(
                status_code="EXCEEDED", color_hex="#FF0000"
            )  # 붉은색 (임계 초과)
