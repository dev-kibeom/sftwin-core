"""
[File Summary]
JaxRlPlannerAdapter
JAX/Flax 기반 RL 에이전트와 POSIX Shared Memory(IPC)로 통신하는 구체적 인프라 어댑터입니다.
"""


class JaxRlPlannerAdapter:
    def __init__(self):
        self._shm_descriptor = 1  # Dummy Descriptor

    def plan_bypass_trajectory(self, obstacle: dict) -> list:
        """
        POSIX SHM을 통해 C++ RL 에이전트와 통신하여 우회 웨이포인트를 반환합니다.
        (런타임에는 CTypes/PyBind11 호출이 발생하며, 단위 테스트에서 모킹됩니다)
        """
        # 실제 환경에서는 IPC 대기 후 좌표 리스트 반환
        return [{"x": 1.2, "y": 3.4}, {"x": 1.5, "y": 3.6}]
