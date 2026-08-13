#!/bin/bash
set -e

# plugins/protobuf_codec 디렉토리 기준 상대 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROTO_DIR="${PLUGIN_ROOT}/proto"

echo "=========================================================="
echo " Generating Protobuf Stubs (C++ & Python) for Plugins"
echo "=========================================================="

# 1. Python Protobuf Stub 생성 (plugins/protobuf_codec/python_gen 디렉터리로 분리)
mkdir -p "${PLUGIN_ROOT}/python_gen"
python3 -m grpc_tools.protoc \
    -I="${PROTO_DIR}" \
    --python_out="${PLUGIN_ROOT}/python_gen" \
    "${PROTO_DIR}"/*.proto

# 2. C++ Protobuf Header/Source 생성 (plugins/protobuf_codec/cpp_gen 디렉터리로 분리)
mkdir -p "${PLUGIN_ROOT}/cpp_gen"
protoc \
    --experimental_allow_proto3_optional \
    -I="${PROTO_DIR}" \
    --cpp_out="${PLUGIN_ROOT}/cpp_gen" \
    "${PROTO_DIR}"/*.proto

echo "Successfully generated Protobuf stubs in:"
echo " - Python: ${PLUGIN_ROOT}/python_gen"
echo " - C++:    ${PLUGIN_ROOT}/cpp_gen"
