#!/bin/bash
set -e

WS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$WS_DIR"

INPUT_PATH=$1

# 1. 인터페이스 패키지가 존재하면 항상 최우선으로 빌드 및 환경 로드
if [ -d "src/interfaces" ]; then
    echo "=== [1/3] Building interfaces (src/interfaces) ==="
    colcon build --base-paths src/interfaces
    source install/setup.bash
elif [ -f "install/setup.bash" ]; then
    source install/setup.bash
fi

# 2. 타깃 경로 처리
if [ -z "$INPUT_PATH" ]; then
    echo "=== [2/3] Building all packages in workspace (src/) ==="
    TARGET_PATH="src"
else
    CLEAN_PATH="${INPUT_PATH%/}"
    if [[ "$CLEAN_PATH" == src/* ]]; then
        TARGET_PATH="$CLEAN_PATH"
    elif [[ "$CLEAN_PATH" == "src" ]]; then
        TARGET_PATH="src"
    else
        TARGET_PATH="src/$CLEAN_PATH"
    fi

    if [ ! -d "$TARGET_PATH" ]; then
        echo "Error: Directory '$TARGET_PATH' does not exist."
        exit 1
    fi
    echo "=== [2/3] Building target: $TARGET_PATH ==="
fi

# 3. 대상 모듈 빌드
colcon build --base-paths "$TARGET_PATH" --cmake-args -DBUILD_TESTING=ON
source install/setup.bash

# 4. 테스트 실행
echo "=== [3/3] Running tests for: $TARGET_PATH ==="
colcon test --base-paths "$TARGET_PATH" --ctest-args -E "(cpplint|uncrustify|copyright|lint_cmake|xmllint)" --event-handlers console_direct+

# 5. 결과 요약
colcon test-result --verbose
