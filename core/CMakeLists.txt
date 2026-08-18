# core/CMakeLists.txt
cmake_minimum_required(VERSION 3.14)
project(sftwin_core CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 공통 3rd-party 의존성 로드
find_package(GTest REQUIRED)
find_package(spdlog REQUIRED)
find_package(fmt REQUIRED)

# GMock 타겟 네임스페이스 호환성 처리
if(NOT TARGET GMock::gmock)
    if(TARGET GTest::gmock)
        add_library(GMock::gmock ALIAS GTest::gmock)
    else()
        find_package(GMock REQUIRED)
    endif()
endif()

enable_testing()
include(GoogleTest)

# 💡 1. shared 공통 C++ 소스 수집 및 라이브러리화
file(GLOB_RECURSE SHARED_SRCS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/shared/*.cpp"
)
if(SHARED_SRCS)
    add_library(shared_core STATIC ${SHARED_SRCS})
    target_include_directories(shared_core PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )
    target_link_libraries(shared_core PUBLIC
        spdlog::spdlog
        fmt::fmt
    )
endif()

# 서브디렉터리 추가
add_subdirectory(src/edge_control)
# add_subdirectory(src/simulation)
