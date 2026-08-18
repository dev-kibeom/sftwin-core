from enum import Enum


class DeployPackageFormat(str, Enum):
    ROS2_WS = "ROS2_WS"
    VDA_5050 = "VDA_5050"
    OPEN_RMF = "OPEN_RMF"
