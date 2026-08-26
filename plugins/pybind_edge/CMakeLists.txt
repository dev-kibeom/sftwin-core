cmake_minimum_required(VERSION 3.16)
project(edge_control_pybind)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 1. Python 및 pybind11 패키지 탐색
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# 2. Pybind11 모듈 타깃 생성
pybind11_add_module(edge_control_pybind
    src/edge_facade_pybind.cpp
)

# 3. Include 경로 설정
target_include_directories(edge_control_pybind PRIVATE
    ${PROJECT_SOURCE_DIR}/../../core/src
    ${PROJECT_SOURCE_DIR}/../../plugins
    ${Python3_INCLUDE_DIRS}
)

# 4. 의존성 라이브러리 링크 (protobuf 플러그인, core 라이브러리 등)
target_link_libraries(edge_control_pybind PRIVATE
    pybind11::module
    Python3::Python
    sftwin_protobuf_codec
    # 필요 시 edge_control 코어 타깃 링크
)
