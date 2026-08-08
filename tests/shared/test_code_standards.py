import ast
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[2] / "src"


def get_target_python_files():
    files = []
    for path in SRC_DIR.rglob("*.py"):
        if "shared" not in path.parts and not path.name.startswith("__"):
            files.append(path)
    return files


@pytest.mark.parametrize(
    "file_path", get_target_python_files(), ids=lambda p: str(p.relative_to(SRC_DIR))
)
def test_global_logging_and_exception_compliance(file_path):
    with open(file_path, encoding="utf-8") as f:
        code_content = f.read()

    tree = ast.parse(code_content, filename=str(file_path))
    relative_path = file_path.relative_to(SRC_DIR)

    forbidden_imports = []
    forbidden_raises = []
    forbidden_calls = []
    domain_violations = []

    for node in ast.walk(tree):
        # 1. 표준 logging import 검사
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "logging":
                    forbidden_imports.append((node.lineno, "import logging"))
                # 도메인 순수성: domain/ 내부에서 외부 라이브러리 import 차단
                if "domain" in relative_path.parts and alias.name in {
                    "fastapi",
                    "sqlalchemy",
                    "redis",
                    "requests",
                }:
                    domain_violations.append((node.lineno, alias.name))

        elif isinstance(node, ast.ImportFrom):
            if node.module == "logging":
                forbidden_imports.append(
                    (node.lineno, f"from logging import {node.names[0].name}")
                )
            if "domain" in relative_path.parts and node.module in {
                "fastapi",
                "sqlalchemy",
                "redis",
                "requests",
            }:
                domain_violations.append((node.lineno, node.module))

        # 2. BaseSystemException 외 원시 예외 raise 검사
        if isinstance(node, ast.Raise) and node.exc is not None:
            if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                exc_name = node.exc.func.id
                if exc_name in {
                    "NotImplementedError",
                    "ValueError",
                    "Exception",
                    "RuntimeError",
                    "KeyError",
                }:
                    forbidden_raises.append((node.lineno, exc_name))

        # 3. 프로덕션 코드 내 print() 사용 검사
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "print":
                forbidden_calls.append((node.lineno, "print()"))

    assert (
        not forbidden_imports
    ), f"[{relative_path}] 표준 logging 모듈 감지: {forbidden_imports}"
    assert (
        not forbidden_raises
    ), f"[{relative_path}] 원시 예외(raise) 감지: {forbidden_raises}"
    assert (
        not forbidden_calls
    ), f"[{relative_path}] print() 호출 감지 (GlobalSystemLogger 사용 필요): {forbidden_calls}"
    assert (
        not domain_violations
    ), f"[{relative_path}] 도메인 계층 내 외부 프레임워크 의존 감지: {domain_violations}"
