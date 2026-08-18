from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OptimizeLayoutRequestDto:
    """설비 배치 최적화 요청 Input DTO"""

    assets: list[dict[str, Any]]
    canvas_bounds: dict[str, float] = field(default_factory=lambda: {"max_x": 50.0})
