from typing import Protocol


class IRecoveryScriptParser(Protocol):
    """BehaviorTree XML, Python Script 등 복구 스크립트 구문 분석 및 검증 포트"""

    def validate_syntax(self, script_content: str) -> bool: ...
