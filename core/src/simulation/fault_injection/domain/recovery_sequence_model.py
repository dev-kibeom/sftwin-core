from dataclasses import dataclass


@dataclass
class RecoverySequenceModel:
    sequence_id: str
    sequence_script: str

    def parse_and_validate(self) -> bool:
        """
        입력된 우회/복구 스크립트 구문이 유효한지 검증합니다.
        """
        if not self.sequence_script or self.sequence_script.strip() == "":
            return False

        # 스크립트 최소 유효 구문 검증 (루트 및 Recovery 태그/명령어 포함 여부)
        return "<root>" in self.sequence_script and "Recovery" in self.sequence_script
