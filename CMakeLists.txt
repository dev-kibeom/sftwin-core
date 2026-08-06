cmake_minimum_required(VERSION 3.14)
project(sftwin_core CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ------------------------------------------------------------------------------
# 1. 의존성 패키지 검색
# ------------------------------------------------------------------------------
find_package(GTest REQUIRED)
find_package(Protobuf REQUIRED)

# [FIX] spdlog 및 fmt 의존성 패키지 검색 추가
find_package(spdlog REQUIRED)
find_package(fmt REQUIRED)

if(NOT TARGET GTest::gmock)
    find_package(GMock REQUIRED)
endif()

# ------------------------------------------------------------------------------
# 2. Proto 파일 자동 탐지 및 커스텀 protoc 빌드 명령 등록
# ------------------------------------------------------------------------------
file(GLOB_RECURSE PROTO_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/*.proto")

set(PROTO_SRCS)
set(PROTO_HDRS)

foreach(PROTO_FILE ${PROTO_FILES})
    get_filename_component(PROTO_NAME ${PROTO_FILE} NAME_WE)
    get_filename_component(PROTO_DIR ${PROTO_FILE} DIRECTORY)
    
    set(PROTO_SRC "${CMAKE_CURRENT_BINARY_DIR}/${PROTO_NAME}.pb.cc")
    set(PROTO_HDR "${CMAKE_CURRENT_BINARY_DIR}/${PROTO_NAME}.pb.h")
    
    # ARGS 내부에서 경로를 따옴표로 감싸지 않고 감싸지 않은 변수 형태로 전달
    add_custom_command(
        OUTPUT ${PROTO_SRC} ${PROTO_HDR}
        COMMAND ${Protobuf_PROTOC_EXECUTABLE}
        ARGS --experimental_allow_proto3_optional
             --cpp_out=${CMAKE_CURRENT_BINARY_DIR}
             -I${PROTO_DIR}
             ${PROTO_FILE}
        DEPENDS ${PROTO_FILE}
        COMMENT "Running protoc on ${PROTO_FILE}"
        VERBATIM
    )
    
    list(APPEND PROTO_SRCS ${PROTO_SRC})
    list(APPEND PROTO_HDRS ${PROTO_HDR})
endforeach()

# ------------------------------------------------------------------------------
# 3. C++ 메인 소스 파일 전체 자동 탐지 (범용 와일드카드)
# ------------------------------------------------------------------------------
# src/ 하위에 어떤 새 컴포넌트 폴더가 추가되어도 모든 .cpp 파일 자동 수집
file(GLOB_RECURSE ALL_CPP_SRCS 
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
)

# ------------------------------------------------------------------------------
# 4. 테스트 파일 전체 자동 탐지 및 실행 파일 빌드
# ------------------------------------------------------------------------------
# tests/ 하위에 추가되는 모든 테스트 .cpp 파일 자동 수집
file(GLOB_RECURSE ALL_TEST_SRCS 
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp"
)

# C++ 단위 테스트 실행 바이너리 생성
add_executable(run_cpp_tests
    ${ALL_TEST_SRCS}
    ${ALL_CPP_SRCS}
    ${PROTO_SRCS}
    ${PROTO_HDRS}
)

# ------------------------------------------------------------------------------
# 5. 헤더 인클루드 경로 및 라이브러리 링크
# ------------------------------------------------------------------------------
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
    # [FIX] spdlog 및 fmt 라이브러리 링크 추가
    spdlog::spdlog
    fmt::fmt
)

enable_testing()
include(GoogleTest)
gtest_discover_tests(run_cpp_tests)