import sys
from pathlib import Path

# core/src 디렉터리를 sys.path 최상단에 주입
tests_dir = Path(__file__).parent
src_dir = tests_dir.parent / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
