#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROTO_DIR="${PROJECT_ROOT}/src/shared/proto"

echo "=========================================================="
echo " Generating Protobuf Stubs (C++ & Python)"
echo "=========================================================="

# 1. Python Protobuf Stub 생성
python3 -m grpc_tools.protoc \
    -I="${PROTO_DIR}" \
    --python_out="${PROTO_DIR}" \
    "${PROTO_DIR}"/*.proto

# 2. C++ Protobuf Header/Source 생성 (build/ 디렉터리로 내보내기)
mkdir -p "${PROJECT_ROOT}/build/proto_gen"
protoc \
    --experimental_allow_proto3_optional \
    -I="${PROTO_DIR}" \
    --cpp_out="${PROJECT_ROOT}/build/proto_gen" \
    "${PROTO_DIR}"/*.proto

echo "Successfully generated Protobuf stubs in:"
echo " - Python: ${PROTO_DIR}"
echo " - C++:    ${PROJECT_ROOT}/build/proto_gen"
