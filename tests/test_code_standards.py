"""
===============================================================================
[File Name] test_code_standards.py
[Location ] /tests/test_code_standards.py
[Description]
 - AST(Abstract Syntax Tree)를 활용하여 정적 코딩 표준 및 아키텍처 규칙을 검사합니다.
   1) 표준 logging 직접 import 금지 (shared 모듈 제외, GlobalSystemLogger 사용 강제)
   2) 원시 예외 raise 금지 (BaseSystemException 강제, 단 Domain 계층 제외)
   3) print() 호출 및 bare except 사용 금지
   4) 클린 아키텍처 계층 간 의존성 방향 원칙 (Dependency Rule)
===============================================================================
"""

import ast
import unittest
from pathlib import Path


class TestCleanArchitectureAndCodeStandards(unittest.TestCase):
    # (Path 객체, ast.AST) 목록 캐싱
    parsed_files: list[tuple[Path, ast.AST]] = []
    project_root: Path

    @classmethod
    def setUpClass(cls):
        # pytest 실행 위치(rootdir) 또는 테스트 파일 위치 기준 프로젝트 루트 확정
        current_file = Path(__file__).resolve()
        # tests/test_code_standards.py 기준 상위 폴더가 프로젝트 루트
        cls.project_root = (
            current_file.parent.parent
            if current_file.parent.name == "tests"
            else current_file.parent
        )

        cls.parsed_files = []
        ignore_names = {
            ".git",
            ".pytest_cache",
            ".venv",
            "venv",
            "build",
            "dist",
            "__pycache__",
            "install",
            "log",
            "data",
            ".egg-info",
        }

        # 프로젝트 하위의 모든 .py 파일 탐색 (단위 테스트 폴더/임시 폴더 제외)
        for py_path in cls.project_root.rglob("*.py"):
            # 제외 대상 디렉터리가 경로에 포함된 경우 스킵
            if any(ign in py_path.parts for ign in ignore_names):
                continue
            # tests 디렉터리 내의 파일은 아키텍처 검사 대상에서 제외
            if "tests" in py_path.parts:
                continue

            try:
                content = py_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_path))
                cls.parsed_files.append((py_path, tree))
            except (SyntaxError, UnicodeDecodeError):
                continue

    def setUp(self):
        self.assertGreater(
            len(self.parsed_files),
            0,
            f"No python files were discovered under '{self.project_root}'.",
        )

    # =========================================================================
    # 1. 로깅 및 예외 처리 준수 검사 (Logging & Exception Compliance)
    # =========================================================================

    def test_no_raw_logging_import_in_src(self):
        """[Rule 1] 비즈니스 모듈 내 표준 logging 모듈의 직접 import를 금지합니다. (shared 인프라 제외)"""
        violations = []
        for file_path, tree in self.parsed_files:
            if "shared" in file_path.parts:
                continue

            rel_path = file_path.relative_to(self.project_root).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "logging" or alias.name.startswith("logging."):
                            violations.append(
                                f"[{rel_path}:{node.lineno}] Direct 'import logging' detected. Use GlobalSystemLogger instead."
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module == "logging" or (
                        node.module and node.module.startswith("logging.")
                    ):
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
        """[Rule 2] 원시 예외 raise를 금지하고 BaseSystemException 사용을 강제합니다. (Domain 계층 제외)"""
        forbidden_raises = {
            "Exception",
            "BaseException",
            "ValueError",
            "TypeError",
            "RuntimeError",
            "KeyError",
            "IndexError",
            "AttributeError",
            "NotImplementedError",
            "FileNotFoundError",
            "IOError",
            "OSError",
        }
        violations = []

        for file_path, tree in self.parsed_files:
            # 도메인 계층 내부 엔티티의 기본 유효성 검사 예외는 허용
            if "domain" in file_path.parts:
                continue

            rel_path = file_path.relative_to(self.project_root).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Raise) and node.exc is not None:
                    exc_node = node.exc
                    if isinstance(exc_node, ast.Call):
                        exc_node = exc_node.func

                    exc_name = None
                    if isinstance(exc_node, ast.Name):
                        exc_name = exc_node.id
                    elif isinstance(exc_node, ast.Attribute):
                        exc_name = exc_node.attr

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
        for file_path, tree in self.parsed_files:
            rel_path = file_path.relative_to(self.project_root).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "print":
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
        for file_path, tree in self.parsed_files:
            rel_path = file_path.relative_to(self.project_root).as_posix()
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
        """[Rule 5] Domain 계층은 Application, DTOs, Adapters, Routers, Facades 및 외부 프레임워크에 의존할 수 없습니다."""
        forbidden_imports = {
            "application",
            "dtos",
            "adapters",
            "routers",
            "facades",
            "fastapi",
            "sqlalchemy",
            "requests",
            "httpx",
            "flask",
            "redis",
            "plugins",
        }
        self._assert_layer_dependencies(
            target_layer_dir="domain",
            forbidden_modules=forbidden_imports,
            layer_name="Domain",
        )

    def test_application_layer_has_no_adapter_dependencies(self):
        """[Rule 6] Application 계층은 Adapters, Routers, Plugins에 직접 의존할 수 없습니다."""
        forbidden_imports = {"adapters", "routers", "plugins"}
        self._assert_layer_dependencies(
            target_layer_dir="application",
            forbidden_modules=forbidden_imports,
            layer_name="Application",
        )

    def test_ports_layer_has_no_adapter_dependencies(self):
        """[Rule 7] Ports 계층은 구체 구현체인 Adapters에 의존할 수 없습니다."""
        forbidden_imports = {"adapters", "routers", "plugins"}
        self._assert_layer_dependencies(
            target_layer_dir="ports",
            forbidden_modules=forbidden_imports,
            layer_name="Ports",
        )

    def test_dtos_do_not_import_adapters_or_usecases(self):
        """[Rule 8] DTO는 Adapters나 Routers에 역의존성을 가질 수 없습니다."""
        forbidden_imports = {"adapters", "routers", "plugins"}
        self._assert_layer_dependencies(
            target_layer_dir="dtos",
            forbidden_modules=forbidden_imports,
            layer_name="DTO",
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _assert_layer_dependencies(
        self, target_layer_dir: str, forbidden_modules: set[str], layer_name: str
    ):
        violations = []

        for file_path, tree in self.parsed_files:
            # 경로 구성 요소 중 target_layer_dir ('domain', 'application' 등) 포함 여부 확인
            if target_layer_dir in file_path.parts:
                rel_path = file_path.relative_to(self.project_root).as_posix()
                imports = self._extract_imports(file_path, tree)

                for imp, lineno in imports:
                    imp_segments = set(imp.split("."))
                    matched = imp_segments.intersection(forbidden_modules)
                    if matched:
                        violations.append(
                            f"[{rel_path}:{lineno}] {layer_name} layer imports forbidden package/module '{imp}' (violating keyword: {sorted(list(matched))})"
                        )

        self.assertEqual(
            len(violations),
            0,
            f"\nClean Architecture Violation in {layer_name} Layer:\n"
            + "\n".join(violations),
        )

    def _extract_imports(self, file_path: Path, tree: ast.AST) -> list[tuple[str, int]]:
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, node.lineno))

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""

                if node.level > 0:
                    # 상대 경로 import
                    # level 1은 파일이 속한 디렉터리, level 2는 상위 디렉터리
                    parent_parts = file_path.parent.parts
                    trim = node.level - 1
                    base_parts = parent_parts[:-trim] if trim > 0 else parent_parts
                    prefix = ".".join(base_parts)
                    resolved = f"{prefix}.{module_name}" if module_name else prefix

                    for alias in node.names:
                        imports.append((f"{resolved}.{alias.name}", node.lineno))
                else:
                    # 절대 경로 import
                    if module_name:
                        for alias in node.names:
                            imports.append((f"{module_name}.{alias.name}", node.lineno))
                        # 모듈 자체도 추가 (e.g. kpi_b2b.b2b_procurement.application...)
                        imports.append((module_name, node.lineno))
                    else:
                        for alias in node.names:
                            imports.append((alias.name, node.lineno))

        return imports


if __name__ == "__main__":
    unittest.main()
