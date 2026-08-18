from enum import Enum


class FactoryPhase(str, Enum):
    BASELINE = "BASELINE"
    FMS_OPTIMIZED = "FMS_OPTIMIZED"
