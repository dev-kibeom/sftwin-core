#!/bin/bash
set -e

# 1. 빌드 폴더 준비
mkdir -p build
cd build

# 2. CMake 구성 및 자동 파일 스캔 (새로운 파일 추가 시 cmake 재구성)
cmake .. > /dev/null

# 3. 병렬 빌드 실행
make run_cpp_tests -j$(nproc)

# 4. C++ 테스트 실행
echo -e "\n==================== [ C++ Unit Tests Running ] ===================="
./run_cpp_tests
