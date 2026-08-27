from enum import Enum


class SimulationState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSE = "PAUSE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
