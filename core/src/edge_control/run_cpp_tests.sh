#!/bin/bash
set -e

# 스크립트 위치 기준 경로 자동 산출
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${CORE_ROOT}/build"

echo "=========================================================="
echo " 🚀 Building & Running [edge_control] Unit Tests"
echo "=========================================================="

# 1. 빌드 디렉터리 생성 및 CMake 구성
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

cmake "${CORE_ROOT}" -DCMAKE_BUILD_TYPE=Debug

# 2. edge_control_tests 타겟만 선택적 병렬 빌드
make edge_control_tests -j$(nproc)

# 3. GTest 실행
echo "=========================================================="
echo " 🧪 Running Google Test Suite"
echo "=========================================================="
./src/edge_control/edge_control_tests "$@"
