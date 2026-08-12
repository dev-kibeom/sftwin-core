"""
===============================================================================
[File Name] test_code_standards.py
[Location ] /tests/shared/test_code_standards.py
[Description]
 - AST(Abstract Syntax Tree)를 활용하여 정적 코딩 표준 및 아키텍처 규칙을 검사합니다.
   1) 표준 logging 직접 import 금지 (shared 모듈 제외, GlobalSystemLogger 사용 강제)
   2) 원시 예외 raise 금지 (BaseSystemException 강제)
   3) print() 호출 및 bare except 사용 금지
   4) 클린 아키텍처 계층 간 의존성 방향 원칙 (Dependency Rule)
===============================================================================
"""

import ast
import os
import unittest


class TestCleanArchitectureAndCodeStandards(unittest.TestCase):
    def setUp(self):
        self.src_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../src")
        )

    # =========================================================================
    # 1. 로깅 및 예외 처리 준수 검사 (Logging & Exception Compliance)
    # =========================================================================

    def test_no_raw_logging_import_in_src(self):
        """[Rule 1] 비즈니스 모듈 내 표준 logging 모듈의 직접 import를 금지합니다. (shared 인프라 제외)"""
        violations = []
        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.src_dir)

                    # shared 디렉터리 내부 하부 구조는 인프라 유틸리티이므로 원시 logging 허용
                    if rel_path.startswith("shared/"):
                        continue

                    with open(filepath, encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read(), filename=filepath)
                        except SyntaxError:
                            continue

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name == "logging":
                                    violations.append(
                                        f"[{rel_path}:{node.lineno}] Direct 'import logging' detected. Use GlobalSystemLogger instead."
                                    )
                        elif isinstance(node, ast.ImportFrom):
                            if node.module == "logging":
                                violations.append(
                                    f"[{rel_path}:{node.lineno}] Direct 'from logging import ...' detected. Use GlobalSystemLogger instead."
                                )

        self.assertEqual(
            len(violations),
            0,
            "\nCode Standard Violation - Raw logging import detected:\n"
            + "\n".join(violations),
        )

    def test_no_raw_exception_raises_in_src(self):
        """[Rule 2] 원시 예외(ValueError, RuntimeError 등) raise를 금지하고 BaseSystemException 사용을 강제합니다."""
        forbidden_raises = {
            "NotImplementedError",
            "ValueError",
            "Exception",
            "RuntimeError",
            "KeyError",
        }
        violations = []

        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.src_dir)

                    with open(filepath, encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read(), filename=filepath)
                        except SyntaxError:
                            continue

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Raise) and node.exc is not None:
                            if isinstance(node.exc, ast.Call) and isinstance(
                                node.exc.func, ast.Name
                            ):
                                exc_name = node.exc.func.id
                                if exc_name in forbidden_raises:
                                    violations.append(
                                        f"[{rel_path}:{node.lineno}] Raw raise '{exc_name}' detected. Use BaseSystemException instead."
                                    )

        self.assertEqual(
            len(violations),
            0,
            "\nCode Standard Violation - Raw Exception raises detected:\n"
            + "\n".join(violations),
        )

    def test_no_raw_print_statements_in_src(self):
        """[Rule 3] 디버깅용 raw print() 사용을 금지합니다."""
        violations = []
        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.src_dir)

                    with open(filepath, encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read(), filename=filepath)
                        except SyntaxError:
                            continue

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if (
                                isinstance(node.func, ast.Name)
                                and node.func.id == "print"
                            ):
                                violations.append(
                                    f"[{rel_path}:{node.lineno}] Raw print() call detected. Use GlobalSystemLogger instead."
                                )

        self.assertEqual(
            len(violations),
            0,
            "\nCode Standard Violation - Raw print() detected:\n"
            + "\n".join(violations),
        )

    def test_no_bare_except_clauses_in_src(self):
        """[Rule 4] bare except: 구문 사용을 금지합니다."""
        violations = []
        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.src_dir)

                    with open(filepath, encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read(), filename=filepath)
                        except SyntaxError:
                            continue

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ExceptHandler):
                            if node.type is None:
                                violations.append(
                                    f"[{rel_path}:{node.lineno}] Bare except: clause detected. Catch explicit Exception or BaseSystemException."
                                )

        self.assertEqual(
            len(violations),
            0,
            "\nCode Standard Violation - Bare except clause detected:\n"
            + "\n".join(violations),
        )

    # =========================================================================
    # 2. 클린 아키텍처 계층 의존성 검사 (Dependency Rules)
    # =========================================================================

    def test_domain_layer_has_no_outer_dependencies(self):
        """[Rule 5] Domain 계층은 Adapters, Routers, Facades 및 외부 프레임워크에 의존할 수 없습니다."""
        forbidden_imports = [
            "adapters",
            "routers",
            "facades",
            "fastapi",
            "sqlalchemy",
            "requests",
            "httpx",
            "flask",
            "redis",
        ]
        violations = []

        for root, _, files in os.walk(self.src_dir):
            if "/domain" in root:
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        filepath = os.path.join(root, file)
                        rel_path = os.path.relpath(filepath, self.src_dir)
                        imports = self._extract_imports(filepath)

                        for imp, lineno in imports:
                            for forbidden in forbidden_imports:
                                if forbidden in imp.split("."):
                                    violations.append(
                                        f"[{rel_path}:{lineno}] Domain layer imports forbidden module '{imp}'"
                                    )

        self.assertEqual(
            len(violations),
            0,
            "\nClean Architecture Violation in Domain Layer:\n" + "\n".join(violations),
        )

    def test_application_layer_has_no_adapter_dependencies(self):
        """[Rule 6] Application 계층은 Adapters 및 Routers에 직접 의존할 수 없습니다."""
        forbidden_imports = ["adapters", "routers"]
        violations = []

        for root, _, files in os.walk(self.src_dir):
            if "/application" in root:
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        filepath = os.path.join(root, file)
                        rel_path = os.path.relpath(filepath, self.src_dir)
                        imports = self._extract_imports(filepath)

                        for imp, lineno in imports:
                            for forbidden in forbidden_imports:
                                if forbidden in imp.split("."):
                                    violations.append(
                                        f"[{rel_path}:{lineno}] Application layer imports forbidden module '{imp}'"
                                    )

        self.assertEqual(
            len(violations),
            0,
            "\nClean Architecture Violation in Application Layer:\n"
            + "\n".join(violations),
        )

    def test_ports_layer_has_no_adapter_dependencies(self):
        """[Rule 7] Ports 계층은 구체 구현체인 Adapters에 의존할 수 없습니다."""
        forbidden_imports = ["adapters"]
        violations = []

        for root, _, files in os.walk(self.src_dir):
            if "/ports" in root:
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        filepath = os.path.join(root, file)
                        rel_path = os.path.relpath(filepath, self.src_dir)
                        imports = self._extract_imports(filepath)

                        for imp, lineno in imports:
                            for forbidden in forbidden_imports:
                                if forbidden in imp.split("."):
                                    violations.append(
                                        f"[{rel_path}:{lineno}] Ports layer imports forbidden module '{imp}'"
                                    )

        self.assertEqual(
            len(violations),
            0,
            "\nClean Architecture Violation in Ports Layer:\n" + "\n".join(violations),
        )

    def test_dtos_do_not_import_adapters_or_usecases(self):
        """[Rule 8] DTO(데이터 전달 객체)는 Adapters나 Application UseCase에 순환 의존성을 가질 수 없습니다."""
        forbidden_imports = ["adapters", "application"]
        violations = []

        for root, _, files in os.walk(self.src_dir):
            if "/dtos" in root or root.endswith("/dtos"):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        filepath = os.path.join(root, file)
                        rel_path = os.path.relpath(filepath, self.src_dir)
                        imports = self._extract_imports(filepath)

                        for imp, lineno in imports:
                            for forbidden in forbidden_imports:
                                if forbidden in imp.split("."):
                                    violations.append(
                                        f"[{rel_path}:{lineno}] DTO layer imports forbidden module '{imp}'"
                                    )

        self.assertEqual(
            len(violations),
            0,
            "\nClean Architecture Violation in DTO Layer:\n" + "\n".join(violations),
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _extract_imports(self, filepath: str) -> list[tuple[str, int]]:
        imports = []
        with open(filepath, encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=filepath)
            except SyntaxError:
                return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append((node.module, node.lineno))

        return imports


if __name__ == "__main__":
    unittest.main()
