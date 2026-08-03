"""
[File Summary]
BehaviorTreeModel Domain Entity
XML 기반의 Behavior Tree 구조를 파싱하고 우회 복구 로직의 유효성을 검증하는 도메인 모델입니다.
"""

from dataclasses import dataclass


@dataclass
class BehaviorTreeModel:
    tree_id: str
    xml_structure: str

    def parse_and_validate(self) -> bool:
        """
        [고수준 비즈니스 규칙]
        입력된 XML 구조가 유효한 Behavior Tree 구문을 포함하고 있는지 검증합니다.
        """
        if not self.xml_structure or self.xml_structure.strip() == "":
            return False

        # 실제 파싱 로직 모사 (루트 노드 및 복구 Fallback 노드 포함 여부 확인)
        if (
            "<root>" not in self.xml_structure
            or '<Fallback name="Recovery">' not in self.xml_structure
        ):
            return False

        return True
