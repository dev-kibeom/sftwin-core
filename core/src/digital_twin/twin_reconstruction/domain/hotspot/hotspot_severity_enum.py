from enum import Enum


class HotspotSeverity(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    EXCEEDED = "EXCEEDED"
