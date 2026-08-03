"""
[File Summary]
DeployPackageFormatEnum
배포 패키지의 포맷(ROS2_WS, VDA_5050, OPEN_RMF)을 정의하는 도메인 열거형입니다.
"""

from enum import Enum


class DeployPackageFormatEnum(str, Enum):
    ROS2_WS = "ROS2_WS"
    VDA_5050 = "VDA_5050"
    OPEN_RMF = "OPEN_RMF"
