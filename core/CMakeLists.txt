cmake_minimum_required(VERSION 3.14)
project(sftwin_core CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ------------------------------------------------------------------------------
# 1. 의존성 패키지 검색
# ------------------------------------------------------------------------------
find_package(GTest REQUIRED)
find_package(Protobuf REQUIRED)
find_package(spdlog REQUIRED)
find_package(fmt REQUIRED)
find_package(pybind11 CONFIG QUIET) # Pybind11 모듈 검색

if(NOT TARGET GTest::gmock)
    find_package(GMock REQUIRED)
endif()

# ------------------------------------------------------------------------------
# 2. Proto 파일 자동 탐지 및 C++ / Python 스텁 자동 생성
# ------------------------------------------------------------------------------
file(GLOB_RECURSE PROTO_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/shared/proto/*.proto")

set(PROTO_SRCS)
set(PROTO_HDRS)
set(PROTO_PY_STUBS)

foreach(PROTO_FILE ${PROTO_FILES})
    get_filename_component(PROTO_NAME ${PROTO_FILE} NAME_WE)

    set(PROTO_SRC "${CMAKE_CURRENT_BINARY_DIR}/${PROTO_NAME}.pb.cc")
    set(PROTO_HDR "${CMAKE_CURRENT_BINARY_DIR}/${PROTO_NAME}.pb.h")
    set(PROTO_PY  "${CMAKE_CURRENT_SOURCE_DIR}/src/shared/proto/${PROTO_NAME}_pb2.py")

    add_custom_command(
        OUTPUT ${PROTO_SRC} ${PROTO_HDR} ${PROTO_PY}
        COMMAND ${Protobuf_PROTOC_EXECUTABLE}
        ARGS --experimental_allow_proto3_optional
             --cpp_out=${CMAKE_CURRENT_BINARY_DIR}
             --python_out=${CMAKE_CURRENT_SOURCE_DIR}/src/shared/proto
             -I${CMAKE_CURRENT_SOURCE_DIR}/src/shared/proto
             ${PROTO_FILE}
        DEPENDS ${PROTO_FILE}
        COMMENT "Generating C++ and Python Protobuf stubs for ${PROTO_NAME}.proto"
        VERBATIM
    )

    list(APPEND PROTO_SRCS ${PROTO_SRC})
    list(APPEND PROTO_HDRS ${PROTO_HDR})
    list(APPEND PROTO_PY_STUBS ${PROTO_PY})
endforeach()

# Custom Target으로 Proto 빌드 그룹화
add_custom_target(generate_proto_stubs DEPENDS ${PROTO_SRCS} ${PROTO_HDRS} ${PROTO_PY_STUBS})

# ------------------------------------------------------------------------------
# 3. C++ 메인 소스 파일 및 테스트 파일 탐지
# ------------------------------------------------------------------------------
# main/pybind 소스를 제외한 C++ 순수 로직 소스만 수집
file(GLOB_RECURSE ALL_CPP_SRCS "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")
list(FILTER ALL_CPP_SRCS EXCLUDE REGEX ".*edge_facade_pybind.cpp$")

file(GLOB_RECURSE ALL_TEST_SRCS "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp")

# ------------------------------------------------------------------------------
# 4. C++ 단위 테스트 바이너리 빌드 (run_cpp_tests)
# ------------------------------------------------------------------------------
add_executable(run_cpp_tests
    ${ALL_TEST_SRCS}
    ${ALL_CPP_SRCS}
    ${PROTO_SRCS}
    ${PROTO_HDRS}
)

add_dependencies(run_cpp_tests generate_proto_stubs)

target_include_directories(run_cpp_tests PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_BINARY_DIR}
)

target_link_libraries(run_cpp_tests PRIVATE
    GTest::gtest
    GTest::gtest_main
    gmock
    ${PROTOBUF_LIBRARIES}
    spdlog::spdlog
    fmt::fmt
)

# ------------------------------------------------------------------------------
# 5. Pybind11 C-Extension 모듈 빌드 타겟 (edge_facade_pybind)
# ------------------------------------------------------------------------------
if(pybind11_FOUND)
    pybind11_add_module(edge_facade_pybind
        src/edge_control/facades/edge_facade_pybind.cpp
        ${ALL_CPP_SRCS}
        ${PROTO_SRCS}
    )

    add_dependencies(edge_facade_pybind generate_proto_stubs)

    target_include_directories(edge_facade_pybind PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/src
        ${CMAKE_CURRENT_BINARY_DIR}
    )

    target_link_libraries(edge_facade_pybind PRIVATE
        ${PROTOBUF_LIBRARIES}
        spdlog::spdlog
        fmt::fmt
    )
endif()

enable_testing()
include(GoogleTest)
gtest_discover_tests(run_cpp_tests)
