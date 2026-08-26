cmake_minimum_required(VERSION 3.16)
project(sftwin_workspace CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 1. Python 및 Pybind11 필수 의존성 탐색
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# 2. 전역 Include 경로 등록 (core/src 및 plugins 포함)
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/core
    ${CMAKE_CURRENT_SOURCE_DIR}/core/src
    ${CMAKE_CURRENT_SOURCE_DIR}/plugins
    ${Python3_INCLUDE_DIRS}
)

# 3. 하위 모듈/서브프로젝트 등록
add_subdirectory(core)
add_subdirectory(plugins/protobuf_codec)
add_subdirectory(plugins/pybind_edge)
