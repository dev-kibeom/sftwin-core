cmake_minimum_required(VERSION 3.14)
project(sftwin_workspace CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 최상위 루트 및 core 디렉토리를 Include 경로에 등록
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/core
)

# 2. 하위 모듈/서브프로젝트 등록
add_subdirectory(core)
add_subdirectory(plugins/protobuf_codec)
